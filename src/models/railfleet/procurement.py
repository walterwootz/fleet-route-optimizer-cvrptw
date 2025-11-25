"""
Procurement models for suppliers and purchase orders.
"""
from sqlalchemy import Column, String, Numeric, Boolean, DateTime, ForeignKey, Text, Integer
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship
from datetime import datetime
import uuid
from enum import Enum as PyEnum
from src.core.database import Base


class PurchaseOrderStatus(str, PyEnum):
    """Purchase order status enumeration."""
    DRAFT = "DRAFT"  # Initial draft
    APPROVED = "APPROVED"  # Approved by manager
    ORDERED = "ORDERED"  # Sent to supplier
    RECEIVED = "RECEIVED"  # Goods received
    CLOSED = "CLOSED"  # Completed and closed


class Supplier(Base):
    """Supplier model for procurement."""

    __tablename__ = "suppliers"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    supplier_code = Column(String(50), unique=True, nullable=False, index=True)
    name = Column(String(255), nullable=False)
    contact_person = Column(String(255), nullable=True)
    email = Column(String(255), nullable=True)
    phone = Column(String(50), nullable=True)
    address = Column(Text, nullable=True)
    vat_id = Column(String(50), nullable=True)  # VAT identification number
    payment_terms = Column(String(100), nullable=True)  # e.g., "NET30", "NET60"
    currency = Column(String(3), nullable=False, default="EUR")
    is_active = Column(Boolean, nullable=False, default=True)
    notes = Column(Text, nullable=True)
    created_at = Column(DateTime, nullable=False, default=datetime.utcnow)
    updated_at = Column(DateTime, nullable=False, default=datetime.utcnow, onupdate=datetime.utcnow)


class PurchaseOrder(Base):
    """Purchase order model."""

    __tablename__ = "purchase_orders"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    po_number = Column(String(50), unique=True, nullable=False, index=True)
    supplier_id = Column(UUID(as_uuid=True), ForeignKey('suppliers.id'), nullable=False, index=True)
    work_order_id = Column(UUID(as_uuid=True), nullable=True, index=True)  # Optional link to work order
    status = Column(String(20), nullable=False, default=PurchaseOrderStatus.DRAFT.value, index=True)
    order_date = Column(DateTime, nullable=True)  # When order was placed
    expected_delivery_date = Column(DateTime, nullable=True)
    received_date = Column(DateTime, nullable=True)  # When goods were received
    delivery_location_id = Column(UUID(as_uuid=True), ForeignKey('stock_locations.id'), nullable=True)
    total_amount = Column(Numeric(12, 2), nullable=False, default=0)
    currency = Column(String(3), nullable=False, default="EUR")
    notes = Column(Text, nullable=True)
    created_by = Column(UUID(as_uuid=True), nullable=True)
    approved_by = Column(UUID(as_uuid=True), nullable=True)
    approved_at = Column(DateTime, nullable=True)
    created_at = Column(DateTime, nullable=False, default=datetime.utcnow)
    updated_at = Column(DateTime, nullable=False, default=datetime.utcnow, onupdate=datetime.utcnow)

    # Relationships
    lines = relationship("PurchaseOrderLine", back_populates="purchase_order", cascade="all, delete-orphan")


class PurchaseOrderLine(Base):
    """Purchase order line item model."""

    __tablename__ = "purchase_order_lines"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    purchase_order_id = Column(UUID(as_uuid=True), ForeignKey('purchase_orders.id', ondelete='CASCADE'), nullable=False, index=True)
    line_number = Column(Integer, nullable=False)  # Sequential line number
    part_no = Column(String(100), ForeignKey('part_inventory.part_no'), nullable=False, index=True)
    description = Column(Text, nullable=True)
    quantity_ordered = Column(Integer, nullable=False)
    quantity_received = Column(Integer, nullable=False, default=0)
    unit_price = Column(Numeric(10, 2), nullable=False)
    line_total = Column(Numeric(12, 2), nullable=False)  # quantity * unit_price
    notes = Column(Text, nullable=True)

    # Relationships
    purchase_order = relationship("PurchaseOrder", back_populates="lines")

    __table_args__ = (
        # Ensure line numbers are unique within a PO
        # Note: This would typically be a unique constraint on (purchase_order_id, line_number)
    )
