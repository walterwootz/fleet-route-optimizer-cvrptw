"""
Finance models for invoice management and budget tracking.
"""
from sqlalchemy import Column, String, Numeric, Boolean, DateTime, ForeignKey, Text, Integer, CheckConstraint
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship
from datetime import datetime
import uuid
from enum import Enum as PyEnum
from src.core.database import Base


class InvoiceStatus(str, PyEnum):
    """Invoice status enumeration."""
    DRAFT = "DRAFT"  # Initial draft
    REVIEWED = "REVIEWED"  # Reviewed by accountant
    APPROVED = "APPROVED"  # Approved for payment
    EXPORTED = "EXPORTED"  # Exported to ERP system


class Invoice(Base):
    """Invoice model for accounts payable."""

    __tablename__ = "invoices"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    invoice_number = Column(String(100), unique=True, nullable=False, index=True)
    supplier_id = Column(UUID(as_uuid=True), ForeignKey('suppliers.id'), nullable=False, index=True)
    purchase_order_id = Column(UUID(as_uuid=True), ForeignKey('purchase_orders.id'), nullable=True, index=True)
    work_order_id = Column(UUID(as_uuid=True), nullable=True, index=True)  # For direct WO charges
    invoice_date = Column(DateTime, nullable=False)
    due_date = Column(DateTime, nullable=True)
    payment_date = Column(DateTime, nullable=True)
    status = Column(String(20), nullable=False, default=InvoiceStatus.DRAFT.value, index=True)
    total_amount = Column(Numeric(12, 2), nullable=False)
    tax_amount = Column(Numeric(12, 2), nullable=False, default=0)
    currency = Column(String(3), nullable=False, default="EUR")
    notes = Column(Text, nullable=True)
    attachment_url = Column(String(500), nullable=True)  # Link to PDF/scan
    created_by = Column(UUID(as_uuid=True), nullable=True)
    reviewed_by = Column(UUID(as_uuid=True), nullable=True)
    reviewed_at = Column(DateTime, nullable=True)
    approved_by = Column(UUID(as_uuid=True), nullable=True)
    approved_at = Column(DateTime, nullable=True)
    created_at = Column(DateTime, nullable=False, default=datetime.utcnow)
    updated_at = Column(DateTime, nullable=False, default=datetime.utcnow, onupdate=datetime.utcnow)

    # Relationships
    lines = relationship("InvoiceLine", back_populates="invoice", cascade="all, delete-orphan")


class InvoiceLine(Base):
    """Invoice line item model with cost allocation."""

    __tablename__ = "invoice_lines"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    invoice_id = Column(UUID(as_uuid=True), ForeignKey('invoices.id', ondelete='CASCADE'), nullable=False, index=True)
    line_number = Column(Integer, nullable=False)
    description = Column(Text, nullable=False)
    part_no = Column(String(100), ForeignKey('part_inventory.part_no'), nullable=True, index=True)
    purchase_order_line_id = Column(UUID(as_uuid=True), ForeignKey('purchase_order_lines.id'), nullable=True)  # Matched PO line
    quantity = Column(Integer, nullable=True)
    unit_price = Column(Numeric(10, 2), nullable=False)
    line_total = Column(Numeric(12, 2), nullable=False)
    tax_amount = Column(Numeric(12, 2), nullable=False, default=0)
    cost_center = Column(String(50), nullable=True)  # Kostenstelle
    cost_bearer = Column(String(50), nullable=True)  # Kostenträger
    account_code = Column(String(50), nullable=True)  # Account/GL code
    variance = Column(Numeric(12, 2), nullable=True)  # Price/quantity variance vs PO
    notes = Column(Text, nullable=True)

    # Relationships
    invoice = relationship("Invoice", back_populates="lines")


class Budget(Base):
    """Budget tracking model."""

    __tablename__ = "budgets"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    period = Column(String(7), nullable=False, index=True)  # YYYY-MM format
    cost_center = Column(String(50), nullable=False, index=True)
    category = Column(String(100), nullable=True)  # Budget category (parts, labor, overhead)
    planned_amount = Column(Numeric(12, 2), nullable=False, default=0)
    forecast_amount = Column(Numeric(12, 2), nullable=False, default=0)
    actual_amount = Column(Numeric(12, 2), nullable=False, default=0)
    currency = Column(String(3), nullable=False, default="EUR")
    notes = Column(Text, nullable=True)
    created_at = Column(DateTime, nullable=False, default=datetime.utcnow)
    updated_at = Column(DateTime, nullable=False, default=datetime.utcnow, onupdate=datetime.utcnow)

    __table_args__ = (
        # Unique constraint on period + cost_center + category
        # In production, use: UniqueConstraint('period', 'cost_center', 'category', name='uq_budget_period_cc_cat')
    )


class CostCenter(Base):
    """Cost center master data."""

    __tablename__ = "cost_centers"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    code = Column(String(50), unique=True, nullable=False, index=True)
    name = Column(String(255), nullable=False)
    parent_code = Column(String(50), nullable=True)  # Hierarchical structure
    is_active = Column(Boolean, nullable=False, default=True)
    notes = Column(Text, nullable=True)
    created_at = Column(DateTime, nullable=False, default=datetime.utcnow)
    updated_at = Column(DateTime, nullable=False, default=datetime.utcnow, onupdate=datetime.utcnow)
