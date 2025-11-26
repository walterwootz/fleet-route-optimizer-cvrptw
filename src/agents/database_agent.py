"""
Database Agent - RailFleet Manager
Spezialisierter Agent für Datenbank-Operationen, Schema-Management und Daten-Synchronisation

Teil des DeepALL Agent-Systems
"""

import logging
from typing import Dict, List, Optional, Any
from datetime import datetime
from sqlalchemy import inspect, text
from sqlalchemy.orm import Session
import os
import sqlite3

from ..core.database_hybrid import engine, get_db, get_database_info, DATABASE_TYPE
from ..models.railfleet.vehicle import Vehicle
from ..models.railfleet.maintenance import MaintenanceTask, WorkOrder
from ..models.railfleet.inventory import Part
from ..models.railfleet.hr import Staff

logger = logging.getLogger(__name__)


class DatabaseAgent:
    """
    Database Agent für RailFleet Manager
    
    Verantwortlichkeiten:
    - Schema-Verwaltung und Migrations
    - Daten-Validierung und Integrität
    - Performance-Optimierung
    - Backup und Recovery
    - Daten-Synchronisation
    """
    
    def __init__(self):
        self.name = "DatabaseAgent"
        self.version = "1.0.0"
        self.status = "active"
        self.db_info = get_database_info()
        logger.info(f"{self.name} v{self.version} initialized")
        logger.info(f"Database: {self.db_info['type'].upper()}")
    
    # ==================== Schema Management ====================
    
    def get_schema_info(self) -> Dict[str, Any]:
        """Gibt vollständige Schema-Informationen zurück"""
        inspector = inspect(engine)
        tables = inspector.get_table_names()
        
        schema_info = {
            "database_type": DATABASE_TYPE,
            "database_info": self.db_info,
            "tables": {},
            "total_tables": len(tables),
            "timestamp": datetime.utcnow().isoformat()
        }
        
        for table in tables:
            columns = inspector.get_columns(table)
            indexes = inspector.get_indexes(table)
            foreign_keys = inspector.get_foreign_keys(table)
            
            schema_info["tables"][table] = {
                "columns": [
                    {
                        "name": col["name"],
                        "type": str(col["type"]),
                        "nullable": col["nullable"],
                        "default": col.get("default")
                    }
                    for col in columns
                ],
                "indexes": [idx["name"] for idx in indexes],
                "foreign_keys": [
                    {
                        "constrained_columns": fk["constrained_columns"],
                        "referred_table": fk["referred_table"],
                        "referred_columns": fk["referred_columns"]
                    }
                    for fk in foreign_keys
                ]
            }
        
        return schema_info
    
    def validate_schema(self) -> Dict[str, Any]:
        """Validiert das Datenbank-Schema"""
        # Mindestens erforderliche Tabellen (Core)
        required_tables = ["vehicles", "maintenance_tasks"]

        # FLEET-ONE Service Tabellen (Phase 1+2)
        fleet_one_tables = [
            "workshops",           # workshop_service
            "staff",               # hr_service
            "transfer_plans",      # transfer_service
            "suppliers",           # procurement_service
            "part_inventory",      # procurement_service
            "document_links"       # docs_service
        ]

        # FLEET-ONE Phase 3 Tabellen (100% Coverage)
        phase3_tables = [
            "tracks",              # workshop_service
            "wo_assignment",       # workshop_service
            "purchase_orders",     # procurement_service
            "purchase_order_lines", # procurement_service
            "invoices",            # finance_service
            "cost_centers",        # finance_service
            "staff_assignments"    # hr_service
        ]

        # Weitere optionale Tabellen
        optional_tables = [
            "work_orders", "workshop_orders",  # maintenance_service
            "parts", "users", "activity_log"   # core
        ]

        try:
            inspector = inspect(engine)
            existing_tables = inspector.get_table_names()
        except Exception as e:
            return {
                "valid": False,
                "error": f"Failed to inspect schema: {str(e)}",
                "missing_tables": required_tables,
                "extra_tables": [],
                "issues": [str(e)]
            }

        validation = {
            "valid": True,
            "missing_tables": [],
            "fleet_one_tables": [],
            "phase3_tables": [],
            "optional_tables": [],
            "extra_tables": [],
            "issues": [],
            "service_coverage": {},
            "coverage_percentage": 0
        }

        # Prüfe erforderliche Tabellen
        for table in required_tables:
            if table not in existing_tables:
                validation["valid"] = False
                validation["missing_tables"].append(table)

        # Prüfe FLEET-ONE Tabellen (Phase 1+2)
        for table in fleet_one_tables:
            if table in existing_tables:
                validation["fleet_one_tables"].append(table)

        # Prüfe Phase 3 Tabellen
        for table in phase3_tables:
            if table in existing_tables:
                validation["phase3_tables"].append(table)

        # Prüfe optionale Tabellen
        for table in optional_tables:
            if table in existing_tables:
                validation["optional_tables"].append(table)

        # Prüfe zusätzliche Tabellen
        all_known_tables = required_tables + fleet_one_tables + phase3_tables + optional_tables
        for table in existing_tables:
            if table not in all_known_tables and not table.startswith("alembic"):
                validation["extra_tables"].append(table)

        validation["total_tables"] = len(existing_tables)

        # Berechne Coverage Percentage
        total_fleet_one_tables = len(fleet_one_tables) + len(phase3_tables)
        implemented_fleet_one = len(validation["fleet_one_tables"]) + len(validation["phase3_tables"])
        validation["coverage_percentage"] = round((implemented_fleet_one / total_fleet_one_tables) * 100, 1) if total_fleet_one_tables > 0 else 0

        # Service Coverage berechnen (mit Phase 3)
        validation["service_coverage"] = {
            "fleet_db": "vehicles" in existing_tables,
            "maintenance_service": "maintenance_tasks" in existing_tables,
            "workshop_service": (
                "workshops" in existing_tables and
                "tracks" in existing_tables and
                "wo_assignment" in existing_tables
            ),
            "transfer_service": "transfer_plans" in existing_tables and "staff" in existing_tables,
            "procurement_service": (
                "suppliers" in existing_tables and
                "part_inventory" in existing_tables and
                "purchase_orders" in existing_tables and
                "purchase_order_lines" in existing_tables
            ),
            "hr_service": "staff" in existing_tables and "staff_assignments" in existing_tables,
            "docs_service": "document_links" in existing_tables,
            "finance_service": (
                "invoices" in existing_tables and
                "cost_centers" in existing_tables
            ),
            "reporting_service": (
                "vehicles" in existing_tables and
                "maintenance_tasks" in existing_tables and
                "workshops" in existing_tables
            )
        }

        return validation
    
    # ==================== Data Operations ====================
    
    def get_statistics(self, db: Session = None) -> Dict[str, Any]:
        """Gibt Datenbank-Statistiken zurück"""
        import sqlite3

        try:
            conn = sqlite3.connect("railfleet.db")
            cursor = conn.cursor()

            # Vehicles
            cursor.execute("SELECT COUNT(*) FROM vehicles")
            total_vehicles = cursor.fetchone()[0]

            cursor.execute("SELECT COUNT(*) FROM vehicles WHERE status = 'operational'")
            operational = cursor.fetchone()[0]

            cursor.execute("SELECT COUNT(*) FROM vehicles WHERE status = 'maintenance_due'")
            maintenance_due = cursor.fetchone()[0]

            cursor.execute("SELECT COUNT(*) FROM vehicles WHERE status = 'in_workshop'")
            in_workshop = cursor.fetchone()[0]

            # Maintenance Tasks
            cursor.execute("SELECT COUNT(*) FROM maintenance_tasks")
            total_tasks = cursor.fetchone()[0]

            # FLEET-ONE Tables (Phase 1+2)
            cursor.execute("SELECT COUNT(*) FROM workshops")
            total_workshops = cursor.fetchone()[0]

            cursor.execute("SELECT COUNT(*) FROM staff")
            total_staff = cursor.fetchone()[0]

            cursor.execute("SELECT COUNT(*) FROM transfer_plans")
            total_transfers = cursor.fetchone()[0]

            cursor.execute("SELECT COUNT(*) FROM suppliers")
            total_suppliers = cursor.fetchone()[0]

            cursor.execute("SELECT COUNT(*) FROM part_inventory")
            total_parts = cursor.fetchone()[0]

            cursor.execute("SELECT COUNT(*) FROM document_links")
            total_documents = cursor.fetchone()[0]

            # Phase 3 Tables
            cursor.execute("SELECT COUNT(*) FROM tracks")
            total_tracks = cursor.fetchone()[0]

            cursor.execute("SELECT COUNT(*) FROM wo_assignment")
            total_wo_assignments = cursor.fetchone()[0]

            cursor.execute("SELECT COUNT(*) FROM purchase_orders")
            total_purchase_orders = cursor.fetchone()[0]

            cursor.execute("SELECT COUNT(*) FROM purchase_order_lines")
            total_po_lines = cursor.fetchone()[0]

            cursor.execute("SELECT COUNT(*) FROM invoices")
            total_invoices = cursor.fetchone()[0]

            cursor.execute("SELECT COUNT(*) FROM cost_centers")
            total_cost_centers = cursor.fetchone()[0]

            cursor.execute("SELECT COUNT(*) FROM staff_assignments")
            total_staff_assignments = cursor.fetchone()[0]

            stats = {
                "vehicles": {
                    "total": total_vehicles,
                    "operational": operational,
                    "maintenance_due": maintenance_due,
                    "in_workshop": in_workshop
                },
                "maintenance_tasks": {
                    "total": total_tasks
                },
                "workshops": {
                    "total": total_workshops
                },
                "staff": {
                    "total": total_staff
                },
                "transfer_plans": {
                    "total": total_transfers
                },
                "suppliers": {
                    "total": total_suppliers
                },
                "part_inventory": {
                    "total": total_parts
                },
                "document_links": {
                    "total": total_documents
                },
                "tracks": {
                    "total": total_tracks
                },
                "wo_assignment": {
                    "total": total_wo_assignments
                },
                "purchase_orders": {
                    "total": total_purchase_orders
                },
                "purchase_order_lines": {
                    "total": total_po_lines
                },
                "invoices": {
                    "total": total_invoices
                },
                "cost_centers": {
                    "total": total_cost_centers
                },
                "staff_assignments": {
                    "total": total_staff_assignments
                },
                "timestamp": datetime.utcnow().isoformat()
            }

            conn.close()
            return stats

        except Exception as e:
            logger.error(f"Statistics failed: {str(e)}")
            return {
                "error": str(e),
                "timestamp": datetime.utcnow().isoformat()
            }
    
    def health_check(self, db: Session = None) -> Dict[str, Any]:
        """Führt einen Gesundheitscheck der Datenbank durch"""
        import sqlite3

        health = {
            "status": "healthy",
            "checks": {},
            "timestamp": datetime.utcnow().isoformat()
        }

        try:
            # Test 1: Verbindung
            conn = sqlite3.connect("railfleet.db")
            cursor = conn.cursor()
            cursor.execute("SELECT 1")
            conn.close()
            health["checks"]["connection"] = "ok"
        except Exception as e:
            health["status"] = "unhealthy"
            health["checks"]["connection"] = f"failed: {str(e)}"

        try:
            # Test 2: Schema-Validierung
            validation = self.validate_schema()
            if validation["valid"]:
                health["checks"]["schema"] = "ok"
            else:
                health["status"] = "degraded"
                health["checks"]["schema"] = f"issues: {validation['missing_tables']}"
        except Exception as e:
            health["status"] = "unhealthy"
            health["checks"]["schema"] = f"failed: {str(e)}"

        try:
            # Test 3: Daten-Integrität
            conn = sqlite3.connect("railfleet.db")
            cursor = conn.cursor()
            cursor.execute("SELECT COUNT(*) FROM vehicles")
            vehicle_count = cursor.fetchone()[0]
            conn.close()
            health["checks"]["data_integrity"] = f"ok ({vehicle_count} vehicles)"
        except Exception as e:
            health["status"] = "unhealthy"
            health["checks"]["data_integrity"] = f"failed: {str(e)}"

        return health

    # ==================== Backup & Recovery ====================

    def create_backup(self, backup_path: str) -> Dict[str, Any]:
        """Erstellt ein Backup der Datenbank"""
        import shutil
        from pathlib import Path

        try:
            timestamp = datetime.utcnow().strftime("%Y%m%d_%H%M%S")
            backup_file = f"railfleet_backup_{timestamp}.db"
            backup_full_path = Path(backup_path) / backup_file

            # Kopiere SQLite-Datei
            shutil.copy2("railfleet.db", backup_full_path)

            return {
                "status": "success",
                "backup_file": str(backup_full_path),
                "timestamp": datetime.utcnow().isoformat(),
                "size_bytes": backup_full_path.stat().st_size
            }
        except Exception as e:
            logger.error(f"Backup failed: {str(e)}")
            return {
                "status": "failed",
                "error": str(e),
                "timestamp": datetime.utcnow().isoformat()
            }

    # ==================== Query Optimization ====================

    def analyze_query_performance(self, db: Session, query_str: str) -> Dict[str, Any]:
        """Analysiert die Performance einer Query"""
        try:
            # SQLite EXPLAIN QUERY PLAN
            explain_result = db.execute(text(f"EXPLAIN QUERY PLAN {query_str}"))
            plan = [dict(row) for row in explain_result]

            return {
                "status": "success",
                "query": query_str,
                "execution_plan": plan,
                "timestamp": datetime.utcnow().isoformat()
            }
        except Exception as e:
            return {
                "status": "failed",
                "error": str(e),
                "timestamp": datetime.utcnow().isoformat()
            }

    # ==================== Data Synchronization ====================

    def sync_status(self, db: Session) -> Dict[str, Any]:
        """Gibt den Synchronisations-Status zurück"""
        # Placeholder für zukünftige Supabase-Sync
        return {
            "local_db": "sqlite",
            "remote_db": "supabase (not connected)",
            "last_sync": None,
            "pending_changes": 0,
            "status": "local_only",
            "timestamp": datetime.utcnow().isoformat()
        }

    # ==================== Agent Interface ====================

    def execute_command(self, command: str, params: Optional[Dict] = None) -> Dict[str, Any]:
        """
        Führt einen Database-Agent-Befehl aus

        Verfügbare Befehle:
        - schema_info: Gibt Schema-Informationen zurück
        - validate: Validiert das Schema
        - stats: Gibt Statistiken zurück
        - health: Führt Health-Check durch
        - backup: Erstellt Backup
        - analyze: Analysiert Query-Performance
        - sync_status: Gibt Sync-Status zurück
        """
        params = params or {}

        try:
            if command == "schema_info":
                return self.get_schema_info()

            elif command == "validate":
                return self.validate_schema()

            elif command == "stats":
                db = next(get_db())
                return self.get_statistics(db)

            elif command == "health":
                db = next(get_db())
                return self.health_check(db)

            elif command == "backup":
                backup_path = params.get("path", "./backups")
                return self.create_backup(backup_path)

            elif command == "analyze":
                db = next(get_db())
                query = params.get("query", "SELECT * FROM vehicles LIMIT 1")
                return self.analyze_query_performance(db, query)

            elif command == "sync_status":
                db = next(get_db())
                return self.sync_status(db)

            else:
                return {
                    "status": "error",
                    "message": f"Unknown command: {command}",
                    "available_commands": [
                        "schema_info", "validate", "stats", "health",
                        "backup", "analyze", "sync_status"
                    ]
                }

        except Exception as e:
            logger.error(f"Command execution failed: {str(e)}")
            return {
                "status": "error",
                "message": str(e),
                "timestamp": datetime.utcnow().isoformat()
            }

    def __repr__(self):
        return f"<DatabaseAgent(name={self.name}, version={self.version}, status={self.status})>"


# Singleton-Instanz
database_agent = DatabaseAgent()


