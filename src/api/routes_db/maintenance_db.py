"""
Maintenance API Routes with Real Database
"""
from fastapi import APIRouter, HTTPException, Query
from typing import List, Optional
from pydantic import BaseModel
from datetime import date, datetime

from src.database import sqlite_db

router = APIRouter(prefix="/api/maintenance", tags=["maintenance"])

# ==================== MODELS ====================

class MaintenanceTaskResponse(BaseModel):
    id: str
    vehicle_id: str
    vehicle_name: str
    series: str
    task_type: str
    due_date: str
    priority: str
    status: str
    description: Optional[str] = None
    completed_date: Optional[str] = None
    created_at: str
    updated_at: str

class MaintenanceTaskCreate(BaseModel):
    vehicle_id: str
    task_type: str
    due_date: str
    priority: str = "medium"
    status: str = "planned"
    description: Optional[str] = None

# ==================== ROUTES ====================

@router.get("/", response_model=List[MaintenanceTaskResponse])
async def get_maintenance_tasks(
    priority: Optional[str] = Query(None, description="Filter by priority"),
    status: Optional[str] = Query(None, description="Filter by status"),
    overdue: Optional[bool] = Query(None, description="Show only overdue tasks")
):
    """Get all maintenance tasks with optional filters"""
    try:
        if overdue:
            tasks = sqlite_db.get_overdue_maintenance()
        elif priority:
            tasks = sqlite_db.get_maintenance_by_priority(priority)
        else:
            tasks = sqlite_db.get_all_maintenance_tasks()
        
        # Filter by status if provided
        if status:
            tasks = [t for t in tasks if t.get('status') == status]
        
        return tasks
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/", response_model=dict)
async def create_maintenance_task(task: MaintenanceTaskCreate):
    """Create new maintenance task"""
    try:
        task_id = sqlite_db.create_maintenance_task(task.dict())
        return {
            "message": "Maintenance task created successfully",
            "task_id": task_id
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/stats/summary")
async def get_maintenance_stats():
    """Get maintenance statistics summary"""
    try:
        all_tasks = sqlite_db.get_all_maintenance_tasks()
        overdue_tasks = sqlite_db.get_overdue_maintenance()
        
        # Count by priority
        by_priority = {}
        by_status = {}
        by_type = {}
        
        for task in all_tasks:
            priority = task.get('priority', 'unknown')
            status = task.get('status', 'unknown')
            task_type = task.get('task_type', 'unknown')
            
            by_priority[priority] = by_priority.get(priority, 0) + 1
            by_status[status] = by_status.get(status, 0) + 1
            by_type[task_type] = by_type.get(task_type, 0) + 1
        
        # Count urgent (due within 7 days)
        today = datetime.now().date()
        urgent = 0
        planned = 0
        
        for task in all_tasks:
            if task.get('status') == 'completed':
                continue
            
            try:
                due_date = datetime.strptime(task['due_date'], '%Y-%m-%d').date()
                days_until = (due_date - today).days
                
                if days_until <= 7 and days_until >= 0:
                    urgent += 1
                elif days_until > 7:
                    planned += 1
            except:
                pass
        
        return {
            "total": len(all_tasks),
            "overdue": len(overdue_tasks),
            "urgent": urgent,
            "planned": planned,
            "by_priority": by_priority,
            "by_status": by_status,
            "by_type": by_type
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/upcoming")
async def get_upcoming_maintenance(days: int = Query(30, description="Days ahead to look")):
    """Get upcoming maintenance tasks"""
    try:
        all_tasks = sqlite_db.get_all_maintenance_tasks()
        today = datetime.now().date()
        
        upcoming = []
        for task in all_tasks:
            if task.get('status') == 'completed':
                continue
            
            try:
                due_date = datetime.strptime(task['due_date'], '%Y-%m-%d').date()
                days_until = (due_date - today).days
                
                if 0 <= days_until <= days:
                    task['days_until'] = days_until
                    upcoming.append(task)
            except:
                pass
        
        # Sort by due date
        upcoming.sort(key=lambda x: x['due_date'])
        
        return upcoming
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/types")
async def get_maintenance_types():
    """Get list of all maintenance types"""
    try:
        tasks = sqlite_db.get_all_maintenance_tasks()
        types = list(set(t.get('task_type') for t in tasks if t.get('task_type')))
        return {"types": sorted(types)}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

