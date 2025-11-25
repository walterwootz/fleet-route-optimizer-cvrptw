"""
Finance endpoints for invoice and budget management.
"""
from fastapi import APIRouter, Depends, HTTPException, status, Query
from sqlalchemy.orm import Session
from sqlalchemy import func
from typing import Optional
from uuid import UUID
from datetime import datetime
from decimal import Decimal
from src.core.database import get_db
from src.models.railfleet.finance import Invoice, InvoiceLine, Budget, CostCenter, InvoiceStatus
from src.models.railfleet.procurement import Supplier, PurchaseOrder, PurchaseOrderLine
from src.models.railfleet.inventory import Part
from src.api.schemas.finance import (
    InvoiceCreate,
    InvoiceUpdate,
    InvoiceResponse,
    InvoiceListResponse,
    InvoiceLineResponse,
    InvoiceMatchRequest,
    InvoiceMatchResponse,
    InvoiceApproveRequest,
    BudgetCreate,
    BudgetUpdate,
    BudgetResponse,
    BudgetListResponse,
    BudgetOverviewResponse,
    BudgetOverviewItem,
    CostCenterCreate,
    CostCenterUpdate,
    CostCenterResponse,
    CostCenterListResponse,
)
from src.api.v1.endpoints.auth import get_current_user
from src.models.railfleet.user import User

router = APIRouter(tags=["Finance"])


# ===== Invoice Endpoints =====

@router.post("/invoices/inbox", response_model=InvoiceResponse, status_code=status.HTTP_201_CREATED)
def create_invoice(
    invoice_data: InvoiceCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """
    Create a new invoice (inbox).

    **Workflow:** DRAFT → REVIEWED → APPROVED → EXPORTED
    **Initial Status:** DRAFT
    """
    # Check if invoice_number already exists
    if db.query(Invoice).filter(Invoice.invoice_number == invoice_data.invoice_number).first():
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Invoice '{invoice_data.invoice_number}' already exists",
        )

    # Validate supplier
    try:
        supplier = db.query(Supplier).filter(Supplier.id == UUID(invoice_data.supplier_id)).first()
        if not supplier:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Supplier '{invoice_data.supplier_id}' not found",
            )
    except ValueError:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Invalid supplier_id UUID format",
        )

    # Calculate totals
    total_amount = sum(line.unit_price * (line.quantity or 1) for line in invoice_data.lines)
    tax_amount = sum(line.tax_amount for line in invoice_data.lines)

    # Create invoice
    new_invoice = Invoice(
        invoice_number=invoice_data.invoice_number,
        supplier_id=UUID(invoice_data.supplier_id),
        purchase_order_id=UUID(invoice_data.purchase_order_id) if invoice_data.purchase_order_id else None,
        work_order_id=UUID(invoice_data.work_order_id) if invoice_data.work_order_id else None,
        invoice_date=invoice_data.invoice_date,
        due_date=invoice_data.due_date,
        currency=invoice_data.currency,
        attachment_url=invoice_data.attachment_url,
        notes=invoice_data.notes,
        total_amount=total_amount,
        tax_amount=tax_amount,
        created_by=current_user.id,
        status=InvoiceStatus.DRAFT.value,
    )
    db.add(new_invoice)
    db.flush()

    # Create lines
    for line_data in invoice_data.lines:
        line_total = line_data.unit_price * (line_data.quantity or 1)
        new_line = InvoiceLine(
            invoice_id=new_invoice.id,
            line_number=line_data.line_number,
            description=line_data.description,
            part_no=line_data.part_no,
            quantity=line_data.quantity,
            unit_price=line_data.unit_price,
            line_total=line_total,
            tax_amount=line_data.tax_amount,
            cost_center=line_data.cost_center,
            cost_bearer=line_data.cost_bearer,
            account_code=line_data.account_code,
        )
        db.add(new_line)

    db.commit()
    db.refresh(new_invoice)

    return _build_invoice_response(new_invoice)


@router.get("/invoices", response_model=InvoiceListResponse)
def list_invoices(
    skip: int = Query(0, ge=0),
    limit: int = Query(100, ge=1, le=1000),
    status: Optional[str] = Query(None, description="Filter by status"),
    supplier_id: Optional[str] = Query(None, description="Filter by supplier UUID"),
    purchase_order_id: Optional[str] = Query(None, description="Filter by PO UUID"),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """List all invoices with optional filtering."""
    query = db.query(Invoice)

    if status:
        query = query.filter(Invoice.status == status)

    if supplier_id:
        try:
            query = query.filter(Invoice.supplier_id == UUID(supplier_id))
        except ValueError:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Invalid supplier_id UUID format",
            )

    if purchase_order_id:
        try:
            query = query.filter(Invoice.purchase_order_id == UUID(purchase_order_id))
        except ValueError:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Invalid purchase_order_id UUID format",
            )

    query = query.order_by(Invoice.invoice_date.desc())

    total = query.count()
    invoices = query.offset(skip).limit(limit).all()

    return InvoiceListResponse(
        total=total,
        invoices=[_build_invoice_response(inv) for inv in invoices],
    )


@router.get("/invoices/{invoice_id}", response_model=InvoiceResponse)
def get_invoice(
    invoice_id: str,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Get invoice by ID or invoice_number."""
    try:
        invoice = db.query(Invoice).filter(Invoice.id == UUID(invoice_id)).first()
    except ValueError:
        invoice = db.query(Invoice).filter(Invoice.invoice_number == invoice_id).first()

    if not invoice:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Invoice '{invoice_id}' not found",
        )

    return _build_invoice_response(invoice)


@router.post("/invoices/{invoice_id}/match", response_model=InvoiceMatchResponse)
def match_invoice(
    invoice_id: str,
    request: InvoiceMatchRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """
    Match invoice lines against PO lines and auto-allocate cost centers.

    **Matching Logic:**
    1. Match invoice lines to PO lines by part_no
    2. Calculate price/quantity variances
    3. Auto-allocate cost centers from PO → WO → Cost Center
    4. Update invoice status to REVIEWED if matching is successful
    """
    try:
        invoice = db.query(Invoice).filter(Invoice.id == UUID(invoice_id)).first()
    except ValueError:
        invoice = db.query(Invoice).filter(Invoice.invoice_number == invoice_id).first()

    if not invoice:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Invoice '{invoice_id}' not found",
        )

    if invoice.status != InvoiceStatus.DRAFT.value:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Cannot match invoice with status '{invoice.status}'. Must be DRAFT.",
        )

    # Get PO if specified
    po = None
    if request.purchase_order_id:
        try:
            po = db.query(PurchaseOrder).filter(PurchaseOrder.id == UUID(request.purchase_order_id)).first()
            if not po:
                raise HTTPException(
                    status_code=status.HTTP_404_NOT_FOUND,
                    detail=f"Purchase order '{request.purchase_order_id}' not found",
                )
        except ValueError:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Invalid purchase_order_id UUID format",
            )

    matched_lines = 0
    unmatched_lines = 0
    total_variance = Decimal(0)

    for inv_line in invoice.lines:
        matched = False

        if po and inv_line.part_no:
            # Try to match against PO lines
            po_line = db.query(PurchaseOrderLine).filter(
                PurchaseOrderLine.purchase_order_id == po.id,
                PurchaseOrderLine.part_no == inv_line.part_no
            ).first()

            if po_line:
                # Calculate variance
                variance = (inv_line.unit_price - po_line.unit_price) * (inv_line.quantity or 1)
                inv_line.variance = variance
                inv_line.purchase_order_line_id = po_line.id
                total_variance += variance
                matched = True
                matched_lines += 1

                # Auto-allocate cost center if requested
                if request.auto_allocate_cost and po.work_order_id:
                    # Simple cost allocation: assume workshop maintenance cost center
                    inv_line.cost_center = "WS-MAINT"  # Default workshop maintenance
                    inv_line.cost_bearer = str(po.work_order_id)[:8]  # First 8 chars of WO ID

        if not matched:
            unmatched_lines += 1

    # Update invoice status to REVIEWED if at least some lines matched
    if matched_lines > 0:
        invoice.status = InvoiceStatus.REVIEWED.value
        invoice.reviewed_by = current_user.id
        invoice.reviewed_at = datetime.utcnow()
        if po:
            invoice.purchase_order_id = po.id

    db.commit()

    return InvoiceMatchResponse(
        invoice_id=str(invoice.id),
        matched_lines=matched_lines,
        unmatched_lines=unmatched_lines,
        total_variance=total_variance,
        message=f"Matched {matched_lines} line(s), {unmatched_lines} unmatched. Total variance: {total_variance:.2f}",
    )


@router.post("/invoices/{invoice_id}/approve", response_model=InvoiceResponse)
def approve_invoice(
    invoice_id: str,
    request: InvoiceApproveRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """
    Approve invoice (REVIEWED → APPROVED).

    **Requires:** Invoice in REVIEWED status
    **Side Effect:** Updates budget actual_amount for affected cost centers
    """
    try:
        invoice = db.query(Invoice).filter(Invoice.id == UUID(invoice_id)).first()
    except ValueError:
        invoice = db.query(Invoice).filter(Invoice.invoice_number == invoice_id).first()

    if not invoice:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Invoice '{invoice_id}' not found",
        )

    if invoice.status != InvoiceStatus.REVIEWED.value:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Cannot approve invoice with status '{invoice.status}'. Must be REVIEWED.",
        )

    # Update invoice status
    invoice.status = InvoiceStatus.APPROVED.value
    invoice.approved_by = current_user.id
    invoice.approved_at = datetime.utcnow()
    if request.notes:
        invoice.notes = (invoice.notes or "") + f"\n[Approval] {request.notes}"

    # Update budget actuals
    period = invoice.invoice_date.strftime("%Y-%m")
    for line in invoice.lines:
        if line.cost_center:
            budget = db.query(Budget).filter(
                Budget.period == period,
                Budget.cost_center == line.cost_center
            ).first()

            if budget:
                budget.actual_amount += line.line_total
            else:
                # Create budget entry if it doesn't exist
                budget = Budget(
                    period=period,
                    cost_center=line.cost_center,
                    category="AUTO",
                    planned_amount=0,
                    forecast_amount=0,
                    actual_amount=line.line_total,
                    currency=invoice.currency,
                )
                db.add(budget)

    db.commit()
    db.refresh(invoice)

    return _build_invoice_response(invoice)


# ===== Budget Endpoints =====

@router.post("/budget", response_model=BudgetResponse, status_code=status.HTTP_201_CREATED)
def create_budget(
    budget_data: BudgetCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Create a new budget entry."""
    # Check for duplicates (period + cost_center + category)
    existing = db.query(Budget).filter(
        Budget.period == budget_data.period,
        Budget.cost_center == budget_data.cost_center,
        Budget.category == budget_data.category
    ).first()

    if existing:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Budget for period '{budget_data.period}', cost center '{budget_data.cost_center}', category '{budget_data.category}' already exists",
        )

    new_budget = Budget(**budget_data.model_dump())
    db.add(new_budget)
    db.commit()
    db.refresh(new_budget)

    return BudgetResponse(
        id=str(new_budget.id),
        **{k: v for k, v in new_budget.__dict__.items() if not k.startswith("_")},
    )


@router.get("/budget/overview", response_model=BudgetOverviewResponse)
def get_budget_overview(
    period: str = Query(..., regex=r'^\d{4}-\d{2}$', description="Period in YYYY-MM format"),
    cost_center: Optional[str] = Query(None, description="Filter by cost center"),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """
    Get budget overview with variance analysis.

    **Features:**
    - Aggregates planned, forecast, and actual amounts
    - Calculates variances (actual - planned)
    - Flags budget overruns (>10% over planned)
    """
    query = db.query(Budget).filter(Budget.period == period)

    if cost_center:
        query = query.filter(Budget.cost_center == cost_center)

    budgets = query.all()

    items = []
    warnings = []
    total_planned = Decimal(0)
    total_actual = Decimal(0)

    for b in budgets:
        variance = b.actual_amount - b.planned_amount
        utilization_pct = float((b.actual_amount / b.planned_amount * 100) if b.planned_amount > 0 else 0)

        items.append(BudgetOverviewItem(
            cost_center=b.cost_center,
            category=b.category,
            planned=b.planned_amount,
            forecast=b.forecast_amount,
            actual=b.actual_amount,
            variance=variance,
            utilization_pct=utilization_pct,
        ))

        total_planned += b.planned_amount
        total_actual += b.actual_amount

        # Flag overruns
        if b.planned_amount > 0 and b.actual_amount > b.planned_amount * Decimal("1.10"):
            warnings.append(
                f"⚠️ Cost center '{b.cost_center}' ({b.category or 'N/A'}): {utilization_pct:.1f}% utilized (over budget)"
            )

    total_variance = total_actual - total_planned

    return BudgetOverviewResponse(
        period=period,
        items=items,
        total_planned=total_planned,
        total_actual=total_actual,
        total_variance=total_variance,
        warnings=warnings,
    )


# ===== Helper Functions =====

def _build_invoice_response(invoice: Invoice) -> InvoiceResponse:
    """Build invoice response with lines."""
    return InvoiceResponse(
        id=str(invoice.id),
        invoice_number=invoice.invoice_number,
        supplier_id=str(invoice.supplier_id),
        purchase_order_id=str(invoice.purchase_order_id) if invoice.purchase_order_id else None,
        work_order_id=str(invoice.work_order_id) if invoice.work_order_id else None,
        invoice_date=invoice.invoice_date,
        due_date=invoice.due_date,
        payment_date=invoice.payment_date,
        status=invoice.status,
        total_amount=invoice.total_amount,
        tax_amount=invoice.tax_amount,
        currency=invoice.currency,
        notes=invoice.notes,
        attachment_url=invoice.attachment_url,
        created_by=str(invoice.created_by) if invoice.created_by else None,
        reviewed_by=str(invoice.reviewed_by) if invoice.reviewed_by else None,
        reviewed_at=invoice.reviewed_at,
        approved_by=str(invoice.approved_by) if invoice.approved_by else None,
        approved_at=invoice.approved_at,
        created_at=invoice.created_at,
        updated_at=invoice.updated_at,
        lines=[
            InvoiceLineResponse(
                id=str(line.id),
                invoice_id=str(line.invoice_id),
                line_number=line.line_number,
                description=line.description,
                part_no=line.part_no,
                quantity=line.quantity,
                unit_price=line.unit_price,
                line_total=line.line_total,
                tax_amount=line.tax_amount,
                cost_center=line.cost_center,
                cost_bearer=line.cost_bearer,
                account_code=line.account_code,
                purchase_order_line_id=str(line.purchase_order_line_id) if line.purchase_order_line_id else None,
                variance=line.variance,
                notes=line.notes,
            )
            for line in invoice.lines
        ],
    )
