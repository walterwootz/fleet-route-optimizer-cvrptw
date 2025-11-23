"""
Procurement schemas for suppliers and purchase orders.
"""
from pydantic import BaseModel, Field, EmailStr
from typing import Optional, List
from datetime import datetime
from decimal import Decimal


# ===== Supplier Schemas =====

class SupplierBase(BaseModel):
    """Base supplier schema."""
    supplier_code: str = Field(..., min_length=1, max_length=50, description="Unique supplier code")
    name: str = Field(..., min_length=1, max_length=255, description="Supplier name")
    contact_person: Optional[str] = Field(None, max_length=255, description="Contact person name")
    email: Optional[str] = Field(None, description="Email address")
    phone: Optional[str] = Field(None, max_length=50, description="Phone number")
    address: Optional[str] = Field(None, description="Physical address")
    vat_id: Optional[str] = Field(None, max_length=50, description="VAT identification number")
    payment_terms: Optional[str] = Field(None, max_length=100, description="Payment terms (e.g., NET30)")
    currency: str = Field("EUR", max_length=3, description="Currency code")
    notes: Optional[str] = Field(None, description="Additional notes")


class SupplierCreate(SupplierBase):
    """Create supplier request."""
    is_active: bool = Field(True, description="Is supplier active")


class SupplierUpdate(BaseModel):
    """Update supplier request (partial updates allowed)."""
    name: Optional[str] = Field(None, min_length=1, max_length=255)
    contact_person: Optional[str] = Field(None, max_length=255)
    email: Optional[str] = None
    phone: Optional[str] = Field(None, max_length=50)
    address: Optional[str] = None
    vat_id: Optional[str] = Field(None, max_length=50)
    payment_terms: Optional[str] = Field(None, max_length=100)
    currency: Optional[str] = Field(None, max_length=3)
    is_active: Optional[bool] = None
    notes: Optional[str] = None


class SupplierResponse(SupplierBase):
    """Supplier response."""
    id: str
    is_active: bool
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True


class SupplierListResponse(BaseModel):
    """List of suppliers response."""
    total: int
    suppliers: List[SupplierResponse]


# ===== Purchase Order Line Schemas =====

class PurchaseOrderLineBase(BaseModel):
    """Base purchase order line schema."""
    line_number: int = Field(..., ge=1, description="Sequential line number")
    part_no: str = Field(..., min_length=1, max_length=100, description="Part number")
    description: Optional[str] = Field(None, description="Line description")
    quantity_ordered: int = Field(..., gt=0, description="Quantity ordered")
    unit_price: Decimal = Field(..., ge=0, description="Unit price")


class PurchaseOrderLineCreate(PurchaseOrderLineBase):
    """Create purchase order line request."""
    pass


class PurchaseOrderLineResponse(PurchaseOrderLineBase):
    """Purchase order line response."""
    id: str
    purchase_order_id: str
    quantity_received: int
    line_total: Decimal
    notes: Optional[str]

    class Config:
        from_attributes = True


# ===== Purchase Order Schemas =====

class PurchaseOrderBase(BaseModel):
    """Base purchase order schema."""
    po_number: str = Field(..., min_length=1, max_length=50, description="Unique PO number")
    supplier_id: str = Field(..., description="Supplier UUID")
    work_order_id: Optional[str] = Field(None, description="Optional work order UUID")
    expected_delivery_date: Optional[datetime] = Field(None, description="Expected delivery date")
    delivery_location_id: Optional[str] = Field(None, description="Delivery stock location UUID")
    currency: str = Field("EUR", max_length=3, description="Currency code")
    notes: Optional[str] = Field(None, description="Additional notes")


class PurchaseOrderCreate(PurchaseOrderBase):
    """Create purchase order request."""
    lines: List[PurchaseOrderLineCreate] = Field(..., min_items=1, description="Order lines")


class PurchaseOrderUpdate(BaseModel):
    """Update purchase order request (partial updates allowed)."""
    supplier_id: Optional[str] = None
    work_order_id: Optional[str] = None
    expected_delivery_date: Optional[datetime] = None
    delivery_location_id: Optional[str] = None
    notes: Optional[str] = None


class PurchaseOrderResponse(PurchaseOrderBase):
    """Purchase order response."""
    id: str
    status: str
    order_date: Optional[datetime]
    received_date: Optional[datetime]
    total_amount: Decimal
    created_by: Optional[str]
    approved_by: Optional[str]
    approved_at: Optional[datetime]
    created_at: datetime
    updated_at: datetime
    lines: List[PurchaseOrderLineResponse] = []

    class Config:
        from_attributes = True


class PurchaseOrderListResponse(BaseModel):
    """List of purchase orders response."""
    total: int
    purchase_orders: List[PurchaseOrderResponse]


# ===== Action Schemas =====

class PurchaseOrderApproveRequest(BaseModel):
    """Approve purchase order request."""
    notes: Optional[str] = Field(None, description="Approval notes")


class PurchaseOrderOrderRequest(BaseModel):
    """Send order to supplier request."""
    order_date: Optional[datetime] = Field(None, description="Order date (defaults to now)")
    notes: Optional[str] = Field(None, description="Order notes")


class PurchaseOrderReceiveRequest(BaseModel):
    """Receive goods request."""
    received_date: Optional[datetime] = Field(None, description="Received date (defaults to now)")
    delivery_location_id: str = Field(..., description="Stock location where goods were received")
    lines_received: List[dict] = Field(
        ...,
        description="List of {line_id: str, quantity_received: int} dictionaries"
    )
    notes: Optional[str] = Field(None, description="Receiving notes")


class PurchaseOrderReceiveResponse(BaseModel):
    """Receive goods response."""
    purchase_order_id: str
    status: str
    stock_moves_created: int
    message: str
