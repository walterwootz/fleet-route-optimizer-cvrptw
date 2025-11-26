"""
Vehicles API Routes with Real Database
"""
from fastapi import APIRouter, HTTPException, Query
from typing import List, Optional
from pydantic import BaseModel
from datetime import date

from src.database import sqlite_db

router = APIRouter(prefix="/api/vehicles", tags=["vehicles"])

# ==================== MODELS ====================

class VehicleResponse(BaseModel):
    id: str
    vehicle_id: str
    series: str
    status: str
    location: Optional[str] = None
    last_maintenance_date: Optional[str] = None
    next_maintenance_due: Optional[str] = None
    mileage: int = 0
    capacity: Optional[int] = None
    workshop_scheduled: bool = False
    created_at: str
    updated_at: str

class VehicleStatusUpdate(BaseModel):
    status: str

# ==================== ROUTES ====================

@router.get("/", response_model=List[VehicleResponse])
async def get_vehicles(
    status: Optional[str] = Query(None, description="Filter by status"),
    location: Optional[str] = Query(None, description="Filter by location")
):
    """Get all vehicles with optional filters"""
    try:
        if status:
            vehicles = sqlite_db.get_vehicles_by_status(status)
        else:
            vehicles = sqlite_db.get_all_vehicles()
        
        # Filter by location if provided
        if location:
            vehicles = [v for v in vehicles if v.get('location') == location]
        
        # Convert workshop_scheduled to boolean
        for v in vehicles:
            v['workshop_scheduled'] = bool(v.get('workshop_scheduled', 0))
        
        return vehicles
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/{vehicle_id}", response_model=VehicleResponse)
async def get_vehicle(vehicle_id: str):
    """Get vehicle by ID"""
    try:
        vehicle = sqlite_db.get_vehicle_by_id(vehicle_id)
        if not vehicle:
            raise HTTPException(status_code=404, detail="Vehicle not found")
        
        vehicle['workshop_scheduled'] = bool(vehicle.get('workshop_scheduled', 0))
        return vehicle
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.patch("/{vehicle_id}/status")
async def update_vehicle_status(vehicle_id: str, update: VehicleStatusUpdate):
    """Update vehicle status"""
    try:
        success = sqlite_db.update_vehicle_status(vehicle_id, update.status)
        if not success:
            raise HTTPException(status_code=404, detail="Vehicle not found")
        
        return {"message": "Status updated successfully", "vehicle_id": vehicle_id, "status": update.status}
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/stats/summary")
async def get_vehicle_stats():
    """Get vehicle statistics summary"""
    try:
        all_vehicles = sqlite_db.get_all_vehicles()
        
        total = len(all_vehicles)
        by_status = {}
        by_location = {}
        
        for v in all_vehicles:
            status = v.get('status', 'unknown')
            location = v.get('location', 'unknown')
            
            by_status[status] = by_status.get(status, 0) + 1
            by_location[location] = by_location.get(location, 0) + 1
        
        # Calculate availability (operational / total)
        operational = by_status.get('operational', 0)
        availability = (operational / total * 100) if total > 0 else 0
        
        return {
            "total": total,
            "operational": operational,
            "availability": round(availability, 1),
            "by_status": by_status,
            "by_location": by_location,
            "workshop_scheduled": sum(1 for v in all_vehicles if v.get('workshop_scheduled'))
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/series/list")
async def get_vehicle_series():
    """Get list of all vehicle series"""
    try:
        vehicles = sqlite_db.get_all_vehicles()
        series = list(set(v.get('series') for v in vehicles if v.get('series')))
        return {"series": sorted(series)}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/locations/list")
async def get_vehicle_locations():
    """Get list of all locations"""
    try:
        vehicles = sqlite_db.get_all_vehicles()
        locations = list(set(v.get('location') for v in vehicles if v.get('location')))
        return {"locations": sorted(locations)}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

