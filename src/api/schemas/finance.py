"""
Finance schemas for invoices, budgets, and cost centers.
"""
from pydantic import BaseModel, Field
from typing import Optional, List
from datetime import datetime
from decimal import Decimal


# ===== Invoice Line Schemas =====

class InvoiceLineBase(BaseModel):
    """Base invoice line schema."""
    line_number: int = Field(..., ge=1, description="Sequential line number")
    description: str = Field(..., min_length=1, description="Line description")
    part_no: Optional[str] = Field(None, max_length=100, description="Part number if applicable")
    quantity: Optional[int] = Field(None, gt=0, description="Quantity")
    unit_price: Decimal = Field(..., ge=0, description="Unit price")
    tax_amount: Decimal = Field(0, ge=0, description="Tax amount")
    cost_center: Optional[str] = Field(None, max_length=50, description="Cost center code")
    cost_bearer: Optional[str] = Field(None, max_length=50, description="Cost bearer code")
    account_code: Optional[str] = Field(None, max_length=50, description="GL account code")


class InvoiceLineCreate(InvoiceLineBase):
    """Create invoice line request."""
    pass


class InvoiceLineResponse(InvoiceLineBase):
    """Invoice line response."""
    id: str
    invoice_id: str
    line_total: Decimal
    purchase_order_line_id: Optional[str]
    variance: Optional[Decimal]
    notes: Optional[str]

    class Config:
        from_attributes = True


# ===== Invoice Schemas =====

class InvoiceBase(BaseModel):
    """Base invoice schema."""
    invoice_number: str = Field(..., min_length=1, max_length=100, description="Unique invoice number")
    supplier_id: str = Field(..., description="Supplier UUID")
    purchase_order_id: Optional[str] = Field(None, description="Optional PO UUID")
    work_order_id: Optional[str] = Field(None, description="Optional work order UUID")
    invoice_date: datetime = Field(..., description="Invoice date")
    due_date: Optional[datetime] = Field(None, description="Payment due date")
    currency: str = Field("EUR", max_length=3, description="Currency code")
    attachment_url: Optional[str] = Field(None, max_length=500, description="Link to PDF/scan")
    notes: Optional[str] = Field(None, description="Additional notes")


class InvoiceCreate(InvoiceBase):
    """Create invoice request."""
    lines: List[InvoiceLineCreate] = Field(..., min_items=1, description="Invoice lines")


class InvoiceUpdate(BaseModel):
    """Update invoice request (partial updates allowed)."""
    supplier_id: Optional[str] = None
    purchase_order_id: Optional[str] = None
    work_order_id: Optional[str] = None
    invoice_date: Optional[datetime] = None
    due_date: Optional[datetime] = None
    payment_date: Optional[datetime] = None
    attachment_url: Optional[str] = None
    notes: Optional[str] = None


class InvoiceResponse(InvoiceBase):
    """Invoice response."""
    id: str
    status: str
    total_amount: Decimal
    tax_amount: Decimal
    payment_date: Optional[datetime]
    created_by: Optional[str]
    reviewed_by: Optional[str]
    reviewed_at: Optional[datetime]
    approved_by: Optional[str]
    approved_at: Optional[datetime]
    created_at: datetime
    updated_at: datetime
    lines: List[InvoiceLineResponse] = []

    class Config:
        from_attributes = True


class InvoiceListResponse(BaseModel):
    """List of invoices response."""
    total: int
    invoices: List[InvoiceResponse]


# ===== Action Schemas =====

class InvoiceMatchRequest(BaseModel):
    """Match invoice against PO/WO request."""
    purchase_order_id: Optional[str] = Field(None, description="PO UUID to match against")
    work_order_id: Optional[str] = Field(None, description="WO UUID to match against")
    auto_allocate_cost: bool = Field(True, description="Automatically allocate cost centers")


class InvoiceMatchResponse(BaseModel):
    """Match invoice response."""
    invoice_id: str
    matched_lines: int
    unmatched_lines: int
    total_variance: Decimal
    message: str


class InvoiceApproveRequest(BaseModel):
    """Approve invoice request."""
    notes: Optional[str] = Field(None, description="Approval notes")


# ===== Budget Schemas =====

class BudgetBase(BaseModel):
    """Base budget schema."""
    period: str = Field(..., pattern=r'^\d{4}-\d{2}$', description="Period in YYYY-MM format")
    cost_center: str = Field(..., min_length=1, max_length=50, description="Cost center code")
    category: Optional[str] = Field(None, max_length=100, description="Budget category")
    planned_amount: Decimal = Field(0, ge=0, description="Planned budget")
    forecast_amount: Decimal = Field(0, ge=0, description="Forecast amount")
    currency: str = Field("EUR", max_length=3, description="Currency code")
    notes: Optional[str] = Field(None, description="Additional notes")


class BudgetCreate(BudgetBase):
    """Create budget request."""
    pass


class BudgetUpdate(BaseModel):
    """Update budget request (partial updates allowed)."""
    planned_amount: Optional[Decimal] = Field(None, ge=0)
    forecast_amount: Optional[Decimal] = Field(None, ge=0)
    actual_amount: Optional[Decimal] = Field(None, ge=0)
    notes: Optional[str] = None


class BudgetResponse(BudgetBase):
    """Budget response."""
    id: str
    actual_amount: Decimal
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True


class BudgetListResponse(BaseModel):
    """List of budgets response."""
    total: int
    budgets: List[BudgetResponse]


class BudgetOverviewItem(BaseModel):
    """Budget overview item."""
    cost_center: str
    category: Optional[str]
    planned: Decimal
    forecast: Decimal
    actual: Decimal
    variance: Decimal  # actual - planned
    utilization_pct: float  # (actual / planned) * 100


class BudgetOverviewResponse(BaseModel):
    """Budget overview response."""
    period: str
    items: List[BudgetOverviewItem]
    total_planned: Decimal
    total_actual: Decimal
    total_variance: Decimal
    warnings: List[str] = []  # Budget overruns


# ===== Cost Center Schemas =====

class CostCenterBase(BaseModel):
    """Base cost center schema."""
    code: str = Field(..., min_length=1, max_length=50, description="Cost center code")
    name: str = Field(..., min_length=1, max_length=255, description="Cost center name")
    parent_code: Optional[str] = Field(None, max_length=50, description="Parent cost center code")
    notes: Optional[str] = Field(None, description="Additional notes")


class CostCenterCreate(CostCenterBase):
    """Create cost center request."""
    is_active: bool = Field(True, description="Is cost center active")


class CostCenterUpdate(BaseModel):
    """Update cost center request (partial updates allowed)."""
    name: Optional[str] = Field(None, min_length=1, max_length=255)
    parent_code: Optional[str] = Field(None, max_length=50)
    is_active: Optional[bool] = None
    notes: Optional[str] = None


class CostCenterResponse(CostCenterBase):
    """Cost center response."""
    id: str
    is_active: bool
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True


class CostCenterListResponse(BaseModel):
    """List of cost centers response."""
    total: int
    cost_centers: List[CostCenterResponse]
