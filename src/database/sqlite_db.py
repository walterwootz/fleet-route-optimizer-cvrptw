"""
SQLite Database Connection for RailFleet Manager
"""
import sqlite3
from typing import List, Dict, Optional, Any
from contextlib import contextmanager
import json
from datetime import datetime

DB_PATH = "railfleet.db"

@contextmanager
def get_db():
    """Get database connection context manager"""
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row  # Return rows as dictionaries
    try:
        yield conn
    finally:
        conn.close()

def dict_from_row(row: sqlite3.Row) -> Dict[str, Any]:
    """Convert SQLite Row to dictionary"""
    return {key: row[key] for key in row.keys()}

# ==================== VEHICLES ====================

def get_all_vehicles() -> List[Dict[str, Any]]:
    """Get all vehicles"""
    with get_db() as conn:
        cursor = conn.cursor()
        cursor.execute("""
            SELECT * FROM vehicles 
            ORDER BY vehicle_id
        """)
        return [dict_from_row(row) for row in cursor.fetchall()]

def get_vehicle_by_id(vehicle_id: str) -> Optional[Dict[str, Any]]:
    """Get vehicle by ID"""
    with get_db() as conn:
        cursor = conn.cursor()
        cursor.execute("SELECT * FROM vehicles WHERE id = ?", (vehicle_id,))
        row = cursor.fetchone()
        return dict_from_row(row) if row else None

def get_vehicles_by_status(status: str) -> List[Dict[str, Any]]:
    """Get vehicles by status"""
    with get_db() as conn:
        cursor = conn.cursor()
        cursor.execute("SELECT * FROM vehicles WHERE status = ?", (status,))
        return [dict_from_row(row) for row in cursor.fetchall()]

def update_vehicle_status(vehicle_id: str, status: str) -> bool:
    """Update vehicle status"""
    with get_db() as conn:
        cursor = conn.cursor()
        cursor.execute("""
            UPDATE vehicles 
            SET status = ?, updated_at = CURRENT_TIMESTAMP 
            WHERE id = ?
        """, (status, vehicle_id))
        conn.commit()
        return cursor.rowcount > 0

# ==================== MAINTENANCE TASKS ====================

def get_all_maintenance_tasks() -> List[Dict[str, Any]]:
    """Get all maintenance tasks with vehicle info"""
    with get_db() as conn:
        cursor = conn.cursor()
        cursor.execute("""
            SELECT 
                m.*,
                v.vehicle_id as vehicle_name,
                v.series
            FROM maintenance_tasks m
            JOIN vehicles v ON m.vehicle_id = v.id
            ORDER BY m.due_date
        """)
        return [dict_from_row(row) for row in cursor.fetchall()]

def get_maintenance_by_priority(priority: str) -> List[Dict[str, Any]]:
    """Get maintenance tasks by priority"""
    with get_db() as conn:
        cursor = conn.cursor()
        cursor.execute("""
            SELECT 
                m.*,
                v.vehicle_id as vehicle_name,
                v.series
            FROM maintenance_tasks m
            JOIN vehicles v ON m.vehicle_id = v.id
            WHERE m.priority = ?
            ORDER BY m.due_date
        """, (priority,))
        return [dict_from_row(row) for row in cursor.fetchall()]

def get_overdue_maintenance() -> List[Dict[str, Any]]:
    """Get overdue maintenance tasks"""
    with get_db() as conn:
        cursor = conn.cursor()
        cursor.execute("""
            SELECT 
                m.*,
                v.vehicle_id as vehicle_name,
                v.series
            FROM maintenance_tasks m
            JOIN vehicles v ON m.vehicle_id = v.id
            WHERE m.due_date < date('now') AND m.status != 'completed'
            ORDER BY m.due_date
        """)
        return [dict_from_row(row) for row in cursor.fetchall()]

def create_maintenance_task(task_data: Dict[str, Any]) -> str:
    """Create new maintenance task"""
    with get_db() as conn:
        cursor = conn.cursor()
        task_id = f"m_{datetime.now().strftime('%Y%m%d%H%M%S')}"
        cursor.execute("""
            INSERT INTO maintenance_tasks 
            (id, vehicle_id, task_type, due_date, priority, status, description)
            VALUES (?, ?, ?, ?, ?, ?, ?)
        """, (
            task_id,
            task_data['vehicle_id'],
            task_data['task_type'],
            task_data['due_date'],
            task_data.get('priority', 'medium'),
            task_data.get('status', 'planned'),
            task_data.get('description', '')
        ))
        conn.commit()
        return task_id

# ==================== WORKSHOP ORDERS ====================

def get_all_workshop_orders() -> List[Dict[str, Any]]:
    """Get all workshop orders with vehicle info"""
    with get_db() as conn:
        cursor = conn.cursor()
        cursor.execute("""
            SELECT 
                w.*,
                v.vehicle_id as vehicle_name,
                v.series
            FROM workshop_orders w
            JOIN vehicles v ON w.vehicle_id = v.id
            ORDER BY w.created_at DESC
        """)
        rows = cursor.fetchall()
        result = []
        for row in rows:
            data = dict_from_row(row)
            # Parse tasks JSON string to array
            if data.get('tasks'):
                try:
                    data['tasks'] = json.loads(data['tasks']) if isinstance(data['tasks'], str) else data['tasks']
                except:
                    data['tasks'] = data['tasks'].split(',') if data['tasks'] else []
            result.append(data)
        return result

def get_workshop_orders_by_status(status: str) -> List[Dict[str, Any]]:
    """Get workshop orders by status"""
    with get_db() as conn:
        cursor = conn.cursor()
        cursor.execute("""
            SELECT 
                w.*,
                v.vehicle_id as vehicle_name
            FROM workshop_orders w
            JOIN vehicles v ON w.vehicle_id = v.id
            WHERE w.status = ?
        """, (status,))
        return [dict_from_row(row) for row in cursor.fetchall()]

def update_workshop_progress(order_id: str, progress: int) -> bool:
    """Update workshop order progress"""
    with get_db() as conn:
        cursor = conn.cursor()
        cursor.execute("""
            UPDATE workshop_orders 
            SET progress = ?, updated_at = CURRENT_TIMESTAMP 
            WHERE id = ?
        """, (progress, order_id))
        conn.commit()
        return cursor.rowcount > 0

