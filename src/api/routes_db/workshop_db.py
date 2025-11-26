"""
Workshop API Routes with Real Database
"""
from fastapi import APIRouter, HTTPException, Query
from typing import List, Optional
from pydantic import BaseModel

from src.database import sqlite_db

router = APIRouter(prefix="/api/workshop", tags=["workshop"])

# ==================== MODELS ====================

class WorkshopOrderResponse(BaseModel):
    id: str
    order_number: str
    vehicle_id: str
    vehicle_name: str
    series: str
    workshop_location: str
    status: str
    tasks: List[str]
    assigned_staff: int
    progress: int
    start_date: Optional[str] = None
    end_date: Optional[str] = None
    created_at: str
    updated_at: str

class WorkshopProgressUpdate(BaseModel):
    progress: int

# ==================== ROUTES ====================

@router.get("/", response_model=List[WorkshopOrderResponse])
async def get_workshop_orders(
    status: Optional[str] = Query(None, description="Filter by status"),
    location: Optional[str] = Query(None, description="Filter by workshop location")
):
    """Get all workshop orders with optional filters"""
    try:
        if status:
            orders = sqlite_db.get_workshop_orders_by_status(status)
        else:
            orders = sqlite_db.get_all_workshop_orders()
        
        # Filter by location if provided
        if location:
            orders = [o for o in orders if o.get('workshop_location') == location]
        
        return orders
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.patch("/{order_id}/progress")
async def update_workshop_progress(order_id: str, update: WorkshopProgressUpdate):
    """Update workshop order progress"""
    try:
        if not 0 <= update.progress <= 100:
            raise HTTPException(status_code=400, detail="Progress must be between 0 and 100")
        
        success = sqlite_db.update_workshop_progress(order_id, update.progress)
        if not success:
            raise HTTPException(status_code=404, detail="Workshop order not found")
        
        return {
            "message": "Progress updated successfully",
            "order_id": order_id,
            "progress": update.progress
        }
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/stats/summary")
async def get_workshop_stats():
    """Get workshop statistics summary"""
    try:
        all_orders = sqlite_db.get_all_workshop_orders()
        
        total = len(all_orders)
        by_status = {}
        by_location = {}
        total_staff = 0
        avg_progress = 0
        
        for order in all_orders:
            status = order.get('status', 'unknown')
            location = order.get('workshop_location', 'unknown')
            
            by_status[status] = by_status.get(status, 0) + 1
            by_location[location] = by_location.get(location, 0) + 1
            total_staff += order.get('assigned_staff', 0)
            avg_progress += order.get('progress', 0)
        
        avg_progress = (avg_progress / total) if total > 0 else 0
        
        return {
            "total": total,
            "by_status": by_status,
            "by_location": by_location,
            "total_staff_assigned": total_staff,
            "average_progress": round(avg_progress, 1)
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/locations")
async def get_workshop_locations():
    """Get list of all workshop locations"""
    try:
        orders = sqlite_db.get_all_workshop_orders()
        locations = list(set(o.get('workshop_location') for o in orders if o.get('workshop_location')))
        return {"locations": sorted(locations)}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/active")
async def get_active_workshops():
    """Get active workshop orders (in_progress status)"""
    try:
        orders = sqlite_db.get_workshop_orders_by_status('in_progress')
        return orders
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

