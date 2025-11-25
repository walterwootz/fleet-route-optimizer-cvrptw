"""
Procurement endpoints for suppliers and purchase orders.
"""
from fastapi import APIRouter, Depends, HTTPException, status, Query
from sqlalchemy.orm import Session
from sqlalchemy import func
from typing import Optional
from uuid import UUID
from datetime import datetime
from src.core.database import get_db
from src.models.railfleet.procurement import Supplier, PurchaseOrder, PurchaseOrderLine, PurchaseOrderStatus
from src.models.railfleet.inventory import Part, StockLocation, StockMove
from src.api.schemas.procurement import (
    SupplierCreate,
    SupplierUpdate,
    SupplierResponse,
    SupplierListResponse,
    PurchaseOrderCreate,
    PurchaseOrderUpdate,
    PurchaseOrderResponse,
    PurchaseOrderListResponse,
    PurchaseOrderLineResponse,
    PurchaseOrderApproveRequest,
    PurchaseOrderOrderRequest,
    PurchaseOrderReceiveRequest,
    PurchaseOrderReceiveResponse,
)
from src.api.v1.endpoints.auth import get_current_user
from src.models.railfleet.user import User

router = APIRouter(tags=["Procurement"])


# ===== Supplier Endpoints =====

@router.post("/suppliers", response_model=SupplierResponse, status_code=status.HTTP_201_CREATED)
def create_supplier(
    supplier_data: SupplierCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """
    Create a new supplier.

    **Requires:** Authentication
    **Fields:**
    - supplier_code: Unique supplier code (required)
    - name: Supplier name (required)
    - payment_terms: e.g., "NET30", "NET60"
    - vat_id: VAT identification number
    """
    # Check if supplier_code already exists
    if db.query(Supplier).filter(Supplier.supplier_code == supplier_data.supplier_code).first():
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Supplier with code '{supplier_data.supplier_code}' already exists",
        )

    new_supplier = Supplier(**supplier_data.model_dump())
    db.add(new_supplier)
    db.commit()
    db.refresh(new_supplier)

    return SupplierResponse(
        id=str(new_supplier.id),
        **{k: v for k, v in new_supplier.__dict__.items() if not k.startswith("_")},
    )


@router.get("/suppliers", response_model=SupplierListResponse)
def list_suppliers(
    skip: int = Query(0, ge=0),
    limit: int = Query(100, ge=1, le=1000),
    is_active: bool = Query(True, description="Filter by active status"),
    search: Optional[str] = Query(None, description="Search by code or name"),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """
    List all suppliers with optional filtering.

    **Query Parameters:**
    - skip: Pagination offset
    - limit: Max results
    - is_active: Filter active/inactive suppliers
    - search: Search in supplier_code or name
    """
    query = db.query(Supplier).filter(Supplier.is_active == is_active)

    if search:
        search_pattern = f"%{search}%"
        query = query.filter(
            (Supplier.supplier_code.ilike(search_pattern)) | (Supplier.name.ilike(search_pattern))
        )

    total = query.count()
    suppliers = query.offset(skip).limit(limit).all()

    return SupplierListResponse(
        total=total,
        suppliers=[
            SupplierResponse(
                id=str(s.id),
                **{k: v for k, v in s.__dict__.items() if not k.startswith("_")},
            )
            for s in suppliers
        ],
    )


@router.get("/suppliers/{supplier_id}", response_model=SupplierResponse)
def get_supplier(
    supplier_id: str,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Get supplier by ID or supplier_code."""
    try:
        supplier = db.query(Supplier).filter(Supplier.id == UUID(supplier_id)).first()
    except ValueError:
        supplier = db.query(Supplier).filter(Supplier.supplier_code == supplier_id).first()

    if not supplier:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Supplier '{supplier_id}' not found",
        )

    return SupplierResponse(
        id=str(supplier.id),
        **{k: v for k, v in supplier.__dict__.items() if not k.startswith("_")},
    )


@router.patch("/suppliers/{supplier_id}", response_model=SupplierResponse)
def update_supplier(
    supplier_id: str,
    supplier_data: SupplierUpdate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Update supplier (partial update)."""
    try:
        supplier = db.query(Supplier).filter(Supplier.id == UUID(supplier_id)).first()
    except ValueError:
        supplier = db.query(Supplier).filter(Supplier.supplier_code == supplier_id).first()

    if not supplier:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Supplier '{supplier_id}' not found",
        )

    update_data = supplier_data.model_dump(exclude_unset=True)
    for field, value in update_data.items():
        setattr(supplier, field, value)

    db.commit()
    db.refresh(supplier)

    return SupplierResponse(
        id=str(supplier.id),
        **{k: v for k, v in supplier.__dict__.items() if not k.startswith("_")},
    )


# ===== Purchase Order Endpoints =====

@router.post("/purchase_orders", response_model=PurchaseOrderResponse, status_code=status.HTTP_201_CREATED)
def create_purchase_order(
    po_data: PurchaseOrderCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """
    Create a new purchase order with lines.

    **Workflow:** DRAFT → APPROVED → ORDERED → RECEIVED → CLOSED
    **Initial Status:** DRAFT
    """
    # Check if po_number already exists
    if db.query(PurchaseOrder).filter(PurchaseOrder.po_number == po_data.po_number).first():
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Purchase order '{po_data.po_number}' already exists",
        )

    # Validate supplier exists
    try:
        supplier = db.query(Supplier).filter(Supplier.id == UUID(po_data.supplier_id)).first()
        if not supplier:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Supplier '{po_data.supplier_id}' not found",
            )
    except ValueError:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Invalid supplier_id UUID format",
        )

    # Validate delivery location if provided
    if po_data.delivery_location_id:
        try:
            location = db.query(StockLocation).filter(StockLocation.id == UUID(po_data.delivery_location_id)).first()
            if not location:
                raise HTTPException(
                    status_code=status.HTTP_404_NOT_FOUND,
                    detail=f"Delivery location '{po_data.delivery_location_id}' not found",
                )
        except ValueError:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Invalid delivery_location_id UUID format",
            )

    # Calculate total amount
    total_amount = sum(line.quantity_ordered * line.unit_price for line in po_data.lines)

    # Create PO
    new_po = PurchaseOrder(
        po_number=po_data.po_number,
        supplier_id=UUID(po_data.supplier_id),
        work_order_id=UUID(po_data.work_order_id) if po_data.work_order_id else None,
        expected_delivery_date=po_data.expected_delivery_date,
        delivery_location_id=UUID(po_data.delivery_location_id) if po_data.delivery_location_id else None,
        currency=po_data.currency,
        notes=po_data.notes,
        total_amount=total_amount,
        created_by=current_user.id,
        status=PurchaseOrderStatus.DRAFT.value,
    )
    db.add(new_po)
    db.flush()  # Get PO id for lines

    # Create lines
    for line_data in po_data.lines:
        # Validate part exists
        part = db.query(Part).filter(Part.part_no == line_data.part_no).first()
        if not part:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Part '{line_data.part_no}' not found",
            )

        line_total = line_data.quantity_ordered * line_data.unit_price
        new_line = PurchaseOrderLine(
            purchase_order_id=new_po.id,
            line_number=line_data.line_number,
            part_no=line_data.part_no,
            description=line_data.description,
            quantity_ordered=line_data.quantity_ordered,
            unit_price=line_data.unit_price,
            line_total=line_total,
        )
        db.add(new_line)

    db.commit()
    db.refresh(new_po)

    # Build response
    return PurchaseOrderResponse(
        id=str(new_po.id),
        po_number=new_po.po_number,
        supplier_id=str(new_po.supplier_id),
        work_order_id=str(new_po.work_order_id) if new_po.work_order_id else None,
        status=new_po.status,
        order_date=new_po.order_date,
        expected_delivery_date=new_po.expected_delivery_date,
        received_date=new_po.received_date,
        delivery_location_id=str(new_po.delivery_location_id) if new_po.delivery_location_id else None,
        total_amount=new_po.total_amount,
        currency=new_po.currency,
        notes=new_po.notes,
        created_by=str(new_po.created_by) if new_po.created_by else None,
        approved_by=str(new_po.approved_by) if new_po.approved_by else None,
        approved_at=new_po.approved_at,
        created_at=new_po.created_at,
        updated_at=new_po.updated_at,
        lines=[
            PurchaseOrderLineResponse(
                id=str(line.id),
                purchase_order_id=str(line.purchase_order_id),
                line_number=line.line_number,
                part_no=line.part_no,
                description=line.description,
                quantity_ordered=line.quantity_ordered,
                quantity_received=line.quantity_received,
                unit_price=line.unit_price,
                line_total=line.line_total,
                notes=line.notes,
            )
            for line in new_po.lines
        ],
    )


@router.get("/purchase_orders", response_model=PurchaseOrderListResponse)
def list_purchase_orders(
    skip: int = Query(0, ge=0),
    limit: int = Query(100, ge=1, le=1000),
    status: Optional[str] = Query(None, description="Filter by status"),
    supplier_id: Optional[str] = Query(None, description="Filter by supplier UUID"),
    work_order_id: Optional[str] = Query(None, description="Filter by work order UUID"),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """
    List all purchase orders with optional filtering.

    **Query Parameters:**
    - skip: Pagination offset
    - limit: Max results
    - status: Filter by DRAFT, APPROVED, ORDERED, RECEIVED, CLOSED
    - supplier_id: Filter by supplier UUID
    - work_order_id: Filter by work order UUID
    """
    query = db.query(PurchaseOrder)

    if status:
        query = query.filter(PurchaseOrder.status == status)

    if supplier_id:
        try:
            query = query.filter(PurchaseOrder.supplier_id == UUID(supplier_id))
        except ValueError:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Invalid supplier_id UUID format",
            )

    if work_order_id:
        try:
            query = query.filter(PurchaseOrder.work_order_id == UUID(work_order_id))
        except ValueError:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Invalid work_order_id UUID format",
            )

    # Order by most recent first
    query = query.order_by(PurchaseOrder.created_at.desc())

    total = query.count()
    purchase_orders = query.offset(skip).limit(limit).all()

    return PurchaseOrderListResponse(
        total=total,
        purchase_orders=[
            PurchaseOrderResponse(
                id=str(po.id),
                po_number=po.po_number,
                supplier_id=str(po.supplier_id),
                work_order_id=str(po.work_order_id) if po.work_order_id else None,
                status=po.status,
                order_date=po.order_date,
                expected_delivery_date=po.expected_delivery_date,
                received_date=po.received_date,
                delivery_location_id=str(po.delivery_location_id) if po.delivery_location_id else None,
                total_amount=po.total_amount,
                currency=po.currency,
                notes=po.notes,
                created_by=str(po.created_by) if po.created_by else None,
                approved_by=str(po.approved_by) if po.approved_by else None,
                approved_at=po.approved_at,
                created_at=po.created_at,
                updated_at=po.updated_at,
                lines=[
                    PurchaseOrderLineResponse(
                        id=str(line.id),
                        purchase_order_id=str(line.purchase_order_id),
                        line_number=line.line_number,
                        part_no=line.part_no,
                        description=line.description,
                        quantity_ordered=line.quantity_ordered,
                        quantity_received=line.quantity_received,
                        unit_price=line.unit_price,
                        line_total=line.line_total,
                        notes=line.notes,
                    )
                    for line in po.lines
                ],
            )
            for po in purchase_orders
        ],
    )


@router.get("/purchase_orders/{po_id}", response_model=PurchaseOrderResponse)
def get_purchase_order(
    po_id: str,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Get purchase order by ID or PO number."""
    try:
        po = db.query(PurchaseOrder).filter(PurchaseOrder.id == UUID(po_id)).first()
    except ValueError:
        po = db.query(PurchaseOrder).filter(PurchaseOrder.po_number == po_id).first()

    if not po:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Purchase order '{po_id}' not found",
        )

    return PurchaseOrderResponse(
        id=str(po.id),
        po_number=po.po_number,
        supplier_id=str(po.supplier_id),
        work_order_id=str(po.work_order_id) if po.work_order_id else None,
        status=po.status,
        order_date=po.order_date,
        expected_delivery_date=po.expected_delivery_date,
        received_date=po.received_date,
        delivery_location_id=str(po.delivery_location_id) if po.delivery_location_id else None,
        total_amount=po.total_amount,
        currency=po.currency,
        notes=po.notes,
        created_by=str(po.created_by) if po.created_by else None,
        approved_by=str(po.approved_by) if po.approved_by else None,
        approved_at=po.approved_at,
        created_at=po.created_at,
        updated_at=po.updated_at,
        lines=[
            PurchaseOrderLineResponse(
                id=str(line.id),
                purchase_order_id=str(line.purchase_order_id),
                line_number=line.line_number,
                part_no=line.part_no,
                description=line.description,
                quantity_ordered=line.quantity_ordered,
                quantity_received=line.quantity_received,
                unit_price=line.unit_price,
                line_total=line.line_total,
                notes=line.notes,
            )
            for line in po.lines
        ],
    )


@router.post("/purchase_orders/{po_id}/approve", response_model=PurchaseOrderResponse)
def approve_purchase_order(
    po_id: str,
    request: PurchaseOrderApproveRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """
    Approve a purchase order (DRAFT → APPROVED).

    **Requires:** Purchase order in DRAFT status
    """
    try:
        po = db.query(PurchaseOrder).filter(PurchaseOrder.id == UUID(po_id)).first()
    except ValueError:
        po = db.query(PurchaseOrder).filter(PurchaseOrder.po_number == po_id).first()

    if not po:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Purchase order '{po_id}' not found",
        )

    if po.status != PurchaseOrderStatus.DRAFT.value:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Cannot approve purchase order with status '{po.status}'. Must be DRAFT.",
        )

    # Update status
    po.status = PurchaseOrderStatus.APPROVED.value
    po.approved_by = current_user.id
    po.approved_at = datetime.utcnow()
    if request.notes:
        po.notes = (po.notes or "") + f"\n[Approval] {request.notes}"

    db.commit()
    db.refresh(po)

    return PurchaseOrderResponse(
        id=str(po.id),
        po_number=po.po_number,
        supplier_id=str(po.supplier_id),
        work_order_id=str(po.work_order_id) if po.work_order_id else None,
        status=po.status,
        order_date=po.order_date,
        expected_delivery_date=po.expected_delivery_date,
        received_date=po.received_date,
        delivery_location_id=str(po.delivery_location_id) if po.delivery_location_id else None,
        total_amount=po.total_amount,
        currency=po.currency,
        notes=po.notes,
        created_by=str(po.created_by) if po.created_by else None,
        approved_by=str(po.approved_by) if po.approved_by else None,
        approved_at=po.approved_at,
        created_at=po.created_at,
        updated_at=po.updated_at,
        lines=[
            PurchaseOrderLineResponse(
                id=str(line.id),
                purchase_order_id=str(line.purchase_order_id),
                line_number=line.line_number,
                part_no=line.part_no,
                description=line.description,
                quantity_ordered=line.quantity_ordered,
                quantity_received=line.quantity_received,
                unit_price=line.unit_price,
                line_total=line.line_total,
                notes=line.notes,
            )
            for line in po.lines
        ],
    )


@router.post("/purchase_orders/{po_id}/order", response_model=PurchaseOrderResponse)
def order_purchase_order(
    po_id: str,
    request: PurchaseOrderOrderRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """
    Send purchase order to supplier (APPROVED → ORDERED).

    **Requires:** Purchase order in APPROVED status
    """
    try:
        po = db.query(PurchaseOrder).filter(PurchaseOrder.id == UUID(po_id)).first()
    except ValueError:
        po = db.query(PurchaseOrder).filter(PurchaseOrder.po_number == po_id).first()

    if not po:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Purchase order '{po_id}' not found",
        )

    if po.status != PurchaseOrderStatus.APPROVED.value:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Cannot order purchase order with status '{po.status}'. Must be APPROVED.",
        )

    # Update status
    po.status = PurchaseOrderStatus.ORDERED.value
    po.order_date = request.order_date or datetime.utcnow()
    if request.notes:
        po.notes = (po.notes or "") + f"\n[Order] {request.notes}"

    db.commit()
    db.refresh(po)

    return PurchaseOrderResponse(
        id=str(po.id),
        po_number=po.po_number,
        supplier_id=str(po.supplier_id),
        work_order_id=str(po.work_order_id) if po.work_order_id else None,
        status=po.status,
        order_date=po.order_date,
        expected_delivery_date=po.expected_delivery_date,
        received_date=po.received_date,
        delivery_location_id=str(po.delivery_location_id) if po.delivery_location_id else None,
        total_amount=po.total_amount,
        currency=po.currency,
        notes=po.notes,
        created_by=str(po.created_by) if po.created_by else None,
        approved_by=str(po.approved_by) if po.approved_by else None,
        approved_at=po.approved_at,
        created_at=po.created_at,
        updated_at=po.updated_at,
        lines=[
            PurchaseOrderLineResponse(
                id=str(line.id),
                purchase_order_id=str(line.purchase_order_id),
                line_number=line.line_number,
                part_no=line.part_no,
                description=line.description,
                quantity_ordered=line.quantity_ordered,
                quantity_received=line.quantity_received,
                unit_price=line.unit_price,
                line_total=line.line_total,
                notes=line.notes,
            )
            for line in po.lines
        ],
    )


@router.post("/purchase_orders/{po_id}/receive", response_model=PurchaseOrderReceiveResponse)
def receive_purchase_order(
    po_id: str,
    request: PurchaseOrderReceiveRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """
    Receive goods from supplier (ORDERED → RECEIVED).

    **This endpoint:**
    1. Updates PO status to RECEIVED
    2. Updates quantity_received for each line
    3. Creates INCOMING stock moves for each received line
    4. Sets received_date

    **Requires:** Purchase order in ORDERED status
    """
    try:
        po = db.query(PurchaseOrder).filter(PurchaseOrder.id == UUID(po_id)).first()
    except ValueError:
        po = db.query(PurchaseOrder).filter(PurchaseOrder.po_number == po_id).first()

    if not po:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Purchase order '{po_id}' not found",
        )

    if po.status != PurchaseOrderStatus.ORDERED.value:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Cannot receive purchase order with status '{po.status}'. Must be ORDERED.",
        )

    # Validate delivery location
    try:
        location = db.query(StockLocation).filter(StockLocation.id == UUID(request.delivery_location_id)).first()
        if not location:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Delivery location '{request.delivery_location_id}' not found",
            )
    except ValueError:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Invalid delivery_location_id UUID format",
        )

    # Process received lines and create stock moves
    stock_moves_created = 0
    for line_received in request.lines_received:
        line_id = line_received.get("line_id")
        quantity_received = line_received.get("quantity_received", 0)

        if not line_id or quantity_received <= 0:
            continue

        # Find line
        try:
            line = db.query(PurchaseOrderLine).filter(
                PurchaseOrderLine.id == UUID(line_id),
                PurchaseOrderLine.purchase_order_id == po.id
            ).first()
        except ValueError:
            continue

        if not line:
            continue

        # Update quantity received
        line.quantity_received += quantity_received

        # Create stock move
        stock_move = StockMove(
            part_no=line.part_no,
            move_type="INCOMING",
            quantity=quantity_received,
            to_location_id=UUID(request.delivery_location_id),
            reference_doc=f"PO-{po.po_number}",
            unit_price=line.unit_price,
            performed_by=current_user.id,
            performed_at=request.received_date or datetime.utcnow(),
            notes=f"Goods receipt from PO {po.po_number}, Line {line.line_number}",
        )
        db.add(stock_move)
        stock_moves_created += 1

    # Update PO status
    po.status = PurchaseOrderStatus.RECEIVED.value
    po.received_date = request.received_date or datetime.utcnow()
    po.delivery_location_id = UUID(request.delivery_location_id)
    if request.notes:
        po.notes = (po.notes or "") + f"\n[Receive] {request.notes}"

    db.commit()

    return PurchaseOrderReceiveResponse(
        purchase_order_id=str(po.id),
        status=po.status,
        stock_moves_created=stock_moves_created,
        message=f"Successfully received {stock_moves_created} line(s) and created stock moves",
    )
