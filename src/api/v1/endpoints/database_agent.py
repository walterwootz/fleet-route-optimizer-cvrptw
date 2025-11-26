"""
Database Agent API Endpoints
Stellt die Database Agent Funktionalität über REST API bereit
"""

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from typing import Dict, Any, Optional
from pydantic import BaseModel

from ....core.database_hybrid import get_db
from ....agents.database_agent import database_agent

router = APIRouter()


class AgentCommand(BaseModel):
    """Schema für Agent-Befehle"""
    command: str
    params: Optional[Dict[str, Any]] = None


@router.get("/status")
async def get_agent_status():
    """
    Gibt den Status des Database Agent zurück
    
    Returns:
        Agent-Status und Informationen
    """
    return {
        "name": database_agent.name,
        "version": database_agent.version,
        "status": database_agent.status,
        "available_commands": [
            "schema_info",
            "validate",
            "stats",
            "health",
            "backup",
            "analyze",
            "sync_status"
        ]
    }


@router.get("/schema")
async def get_schema_info():
    """
    Gibt vollständige Schema-Informationen zurück
    
    Returns:
        Detaillierte Schema-Informationen aller Tabellen
    """
    return database_agent.get_schema_info()


@router.get("/validate")
async def validate_schema():
    """
    Validiert das Datenbank-Schema
    
    Returns:
        Validierungs-Ergebnis mit fehlenden/zusätzlichen Tabellen
    """
    return database_agent.validate_schema()


@router.get("/stats")
async def get_statistics(db: Session = Depends(get_db)):
    """
    Gibt Datenbank-Statistiken zurück
    
    Returns:
        Statistiken über Vehicles, Maintenance, Work Orders, etc.
    """
    return database_agent.get_statistics(db)


@router.get("/health")
async def health_check(db: Session = Depends(get_db)):
    """
    Führt einen Gesundheitscheck der Datenbank durch
    
    Returns:
        Health-Status mit detaillierten Checks
    """
    return database_agent.health_check(db)


@router.post("/backup")
async def create_backup(backup_path: str = "./backups"):
    """
    Erstellt ein Backup der Datenbank
    
    Args:
        backup_path: Pfad für das Backup
        
    Returns:
        Backup-Status und Datei-Informationen
    """
    result = database_agent.create_backup(backup_path)
    
    if result["status"] == "failed":
        raise HTTPException(status_code=500, detail=result["error"])
    
    return result


@router.post("/analyze")
async def analyze_query(
    query: str,
    db: Session = Depends(get_db)
):
    """
    Analysiert die Performance einer Query
    
    Args:
        query: SQL-Query zum Analysieren
        
    Returns:
        Execution Plan und Performance-Informationen
    """
    result = database_agent.analyze_query_performance(db, query)
    
    if result["status"] == "failed":
        raise HTTPException(status_code=400, detail=result["error"])
    
    return result


@router.get("/sync-status")
async def get_sync_status(db: Session = Depends(get_db)):
    """
    Gibt den Synchronisations-Status zurück
    
    Returns:
        Sync-Status zwischen lokaler und Remote-Datenbank
    """
    return database_agent.sync_status(db)


@router.post("/execute")
async def execute_command(command: AgentCommand):
    """
    Führt einen beliebigen Database-Agent-Befehl aus
    
    Args:
        command: Befehl und Parameter
        
    Returns:
        Ergebnis der Befehlsausführung
    """
    result = database_agent.execute_command(
        command.command,
        command.params
    )
    
    if result.get("status") == "error":
        raise HTTPException(status_code=400, detail=result.get("message"))
    
    return result

