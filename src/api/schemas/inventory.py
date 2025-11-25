"""
Inventory schemas for parts, stock locations, and stock moves.
"""
from pydantic import BaseModel, Field
from typing import Optional
from datetime import datetime
from decimal import Decimal


# ===== Part Schemas =====

class PartBase(BaseModel):
    """Base part schema."""
    part_no: str = Field(..., min_length=1, max_length=100, description="Unique part number")
    name: str = Field(..., min_length=1, max_length=255, description="Part name")
    railway_class: Optional[str] = Field(None, description="CRITICAL, STANDARD, or WEAR_PART")
    unit: str = Field("pc", max_length=20, description="Unit of measure (pc, m, kg, l)")
    min_stock: int = Field(0, ge=0, description="Minimum stock level")
    unit_price: Optional[Decimal] = Field(None, ge=0, description="Unit price")
    preferred_supplier_id: Optional[str] = Field(None, description="Preferred supplier UUID")


class PartCreate(PartBase):
    """Create part request."""
    current_stock: int = Field(0, ge=0, description="Initial stock quantity")
    is_active: bool = Field(True, description="Is part active")


class PartUpdate(BaseModel):
    """Update part request (partial updates allowed)."""
    name: Optional[str] = Field(None, min_length=1, max_length=255)
    railway_class: Optional[str] = None
    unit: Optional[str] = Field(None, max_length=20)
    min_stock: Optional[int] = Field(None, ge=0)
    unit_price: Optional[Decimal] = Field(None, ge=0)
    preferred_supplier_id: Optional[str] = None
    is_active: Optional[bool] = None


class PartResponse(PartBase):
    """Part response."""
    id: str
    current_stock: int
    is_active: bool
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True


class PartListResponse(BaseModel):
    """List of parts response."""
    total: int
    parts: list[PartResponse]


# ===== Stock Location Schemas =====

class StockLocationBase(BaseModel):
    """Base stock location schema."""
    location_code: str = Field(..., min_length=1, max_length=50, description="Unique location code")
    name: str = Field(..., min_length=1, max_length=255, description="Location name")
    location_type: str = Field(..., description="WORKSHOP, CENTRAL, TRAIN, or CONSIGNMENT")
    workshop_id: Optional[str] = Field(None, description="Workshop UUID if type is WORKSHOP")
    address: Optional[str] = Field(None, max_length=500, description="Physical address")


class StockLocationCreate(StockLocationBase):
    """Create stock location request."""
    is_active: bool = Field(True, description="Is location active")


class StockLocationUpdate(BaseModel):
    """Update stock location request (partial updates allowed)."""
    name: Optional[str] = Field(None, min_length=1, max_length=255)
    location_type: Optional[str] = None
    workshop_id: Optional[str] = None
    address: Optional[str] = Field(None, max_length=500)
    is_active: Optional[bool] = None


class StockLocationResponse(StockLocationBase):
    """Stock location response."""
    id: str
    is_active: bool
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True


class StockLocationListResponse(BaseModel):
    """List of stock locations response."""
    total: int
    locations: list[StockLocationResponse]


# ===== Stock Move Schemas =====

class StockMoveBase(BaseModel):
    """Base stock move schema."""
    part_no: str = Field(..., min_length=1, max_length=100, description="Part number")
    move_type: str = Field(..., description="INCOMING, USAGE, TRANSFER, WRITEOFF, or ADJUSTMENT")
    quantity: int = Field(..., gt=0, description="Quantity moved")
    from_location_id: Optional[str] = Field(None, description="Source location UUID")
    to_location_id: Optional[str] = Field(None, description="Destination location UUID")
    work_order_id: Optional[str] = Field(None, description="Work order UUID for USAGE moves")
    reference_doc: Optional[str] = Field(None, max_length=255, description="Reference document (PO, invoice)")
    unit_price: Optional[Decimal] = Field(None, ge=0, description="Unit price at time of move")
    notes: Optional[str] = Field(None, max_length=500, description="Additional notes")


class StockMoveCreate(StockMoveBase):
    """Create stock move request."""
    pass


class StockMoveResponse(StockMoveBase):
    """Stock move response."""
    id: str
    performed_by: Optional[str]
    performed_at: datetime

    class Config:
        from_attributes = True


class StockMoveListResponse(BaseModel):
    """List of stock moves response."""
    total: int
    moves: list[StockMoveResponse]


# ===== Stock Overview Schemas =====

class StockOverviewItem(BaseModel):
    """Stock overview for a single part at a location."""
    part_no: str
    part_name: str
    location_code: str
    location_name: str
    quantity: int
    unit: str
    railway_class: Optional[str]


class StockOverviewResponse(BaseModel):
    """Aggregated stock overview response."""
    items: list[StockOverviewItem]
    total_items: int
