"""
Inventory models for parts management, stock locations, and stock moves.
"""
from sqlalchemy import Column, String, Integer, Numeric, Boolean, DateTime, ForeignKey, CheckConstraint
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship
from datetime import datetime
import uuid
from enum import Enum as PyEnum
from src.core.database import Base


class RailwayClass(str, PyEnum):
    """Part criticality classification."""
    CRITICAL = "CRITICAL"  # Critical safety parts
    STANDARD = "STANDARD"  # Standard parts
    WEAR_PART = "WEAR_PART"  # Regular wear parts


class StockMoveType(str, PyEnum):
    """Stock movement types."""
    INCOMING = "INCOMING"  # Wareneingang (goods receipt)
    USAGE = "USAGE"  # Verbauung (consumption in work order)
    TRANSFER = "TRANSFER"  # Umbuchung (transfer between locations)
    WRITEOFF = "WRITEOFF"  # Abschreibung (write-off/scrap)
    ADJUSTMENT = "ADJUSTMENT"  # Inventory adjustment


class Part(Base):
    """Part inventory model (maps to part_inventory table)."""

    __tablename__ = "part_inventory"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    part_no = Column(String(100), unique=True, nullable=False, index=True)
    name = Column(String(255), nullable=False)
    railway_class = Column(String(50), nullable=True)  # CRITICAL, STANDARD, WEAR_PART
    unit = Column(String(20), nullable=False, default="pc")  # pc, m, kg, l, etc.
    min_stock = Column(Integer, nullable=False, default=0)
    current_stock = Column(Integer, nullable=False, default=0)
    preferred_supplier_id = Column(UUID(as_uuid=True), nullable=True)
    unit_price = Column(Numeric(10, 2), nullable=True)
    is_active = Column(Boolean, nullable=False, default=True)
    created_at = Column(DateTime, nullable=False, default=datetime.utcnow)
    updated_at = Column(DateTime, nullable=False, default=datetime.utcnow, onupdate=datetime.utcnow)

    __table_args__ = (
        CheckConstraint('current_stock >= 0', name='part_inv_stock_positive'),
    )


class StockLocation(Base):
    """Stock location model for warehouse management."""

    __tablename__ = "stock_locations"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    location_code = Column(String(50), unique=True, nullable=False, index=True)
    name = Column(String(255), nullable=False)
    location_type = Column(String(50), nullable=False)  # WORKSHOP, CENTRAL, TRAIN, CONSIGNMENT
    workshop_id = Column(UUID(as_uuid=True), nullable=True)  # Link to workshop if applicable
    address = Column(String(500), nullable=True)
    is_active = Column(Boolean, nullable=False, default=True)
    created_at = Column(DateTime, nullable=False, default=datetime.utcnow)
    updated_at = Column(DateTime, nullable=False, default=datetime.utcnow, onupdate=datetime.utcnow)


class StockMove(Base):
    """Stock movement tracking for inventory transactions."""

    __tablename__ = "stock_moves"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    part_no = Column(String(100), ForeignKey('part_inventory.part_no'), nullable=False, index=True)
    move_type = Column(String(50), nullable=False)  # INCOMING, USAGE, TRANSFER, WRITEOFF, ADJUSTMENT
    quantity = Column(Integer, nullable=False)
    from_location_id = Column(UUID(as_uuid=True), ForeignKey('stock_locations.id'), nullable=True)
    to_location_id = Column(UUID(as_uuid=True), ForeignKey('stock_locations.id'), nullable=True)
    work_order_id = Column(UUID(as_uuid=True), nullable=True)  # For USAGE moves
    reference_doc = Column(String(255), nullable=True)  # PO number, invoice, etc.
    unit_price = Column(Numeric(10, 2), nullable=True)
    performed_by = Column(UUID(as_uuid=True), nullable=True)  # User who performed the move
    performed_at = Column(DateTime, nullable=False, default=datetime.utcnow, index=True)
    notes = Column(String(500), nullable=True)

    __table_args__ = (
        CheckConstraint('quantity > 0', name='stock_move_qty_positive'),
    )


class UsedPart(Base):
    """Used parts tracking (legacy table, maps to used_parts)."""

    __tablename__ = "used_parts"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    work_order_id = Column(UUID(as_uuid=True), ForeignKey('work_orders.id', ondelete='CASCADE'), nullable=False, index=True)
    part_no = Column(String(100), ForeignKey('part_inventory.part_no'), nullable=False, index=True)
    quantity_used = Column(Integer, nullable=False)
    unit_price = Column(Numeric(10, 2), nullable=True)
    used_at = Column(DateTime, nullable=False, default=datetime.utcnow, index=True)
    recorded_by = Column(UUID(as_uuid=True), nullable=True)
    notes = Column(String(500), nullable=True)

    __table_args__ = (
        CheckConstraint('quantity_used > 0', name='used_parts_qty_positive'),
    )
