"""Complete Services Schema - Phase 3 Tables

Revision ID: 007_complete_services
Revises: 006_complete_fleet_one
Create Date: 2025-11-25 12:30:00

This migration adds Phase 3 tables for 100% service coverage:
- tracks: Workshop tracks/pits
- wo_assignment: Work order assignments to tracks and teams
- purchase_orders: Purchase orders
- purchase_order_lines: Purchase order line items
- invoices: Financial invoices
- cost_centers: Cost center management
- staff_assignments: Staff assignment tracking
"""

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects.postgresql import UUID, JSONB

# revision identifiers, used by Alembic.
revision = '007_complete_services'
down_revision = '006_complete_fleet_one'
branch_labels = None
depends_on = None


def upgrade():
    """Add Phase 3 tables."""
    
    # 1. tracks - Werkstatt-Gleise/Pits
    op.create_table(
        'tracks',
        sa.Column('id', UUID(as_uuid=True), primary_key=True, server_default=sa.text('gen_random_uuid()')),
        sa.Column('track_id', sa.String(50), unique=True, nullable=False, index=True),
        sa.Column('workshop_id', UUID(as_uuid=True), sa.ForeignKey('workshops.id', ondelete='CASCADE'), nullable=False),
        sa.Column('track_number', sa.Integer, nullable=False),
        sa.Column('capacity', sa.Integer, server_default='1'),
        sa.Column('is_active', sa.Boolean, server_default='true'),
        sa.Column('certifications', JSONB),
        sa.Column('notes', sa.Text),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('NOW()')),
        sa.Column('updated_at', sa.DateTime(timezone=True), server_default=sa.text('NOW()'))
    )
    op.create_index('idx_tracks_workshop', 'tracks', ['workshop_id'])
    op.create_index('idx_tracks_active', 'tracks', ['is_active'])
    
    # 2. wo_assignment - Work Order Assignments
    op.create_table(
        'wo_assignment',
        sa.Column('id', UUID(as_uuid=True), primary_key=True, server_default=sa.text('gen_random_uuid()')),
        sa.Column('work_order_id', UUID(as_uuid=True), sa.ForeignKey('workshop_orders.id', ondelete='CASCADE'), nullable=False),
        sa.Column('track_id', UUID(as_uuid=True), sa.ForeignKey('tracks.id')),
        sa.Column('team_id', UUID(as_uuid=True)),
        sa.Column('assigned_from', sa.DateTime(timezone=True), nullable=False),
        sa.Column('assigned_to', sa.DateTime(timezone=True), nullable=False),
        sa.Column('notes', sa.Text),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('NOW()')),
        sa.Column('updated_at', sa.DateTime(timezone=True), server_default=sa.text('NOW()'))
    )
    op.create_index('idx_wo_assignment_order', 'wo_assignment', ['work_order_id'])
    op.create_index('idx_wo_assignment_track', 'wo_assignment', ['track_id'])
    op.create_index('idx_wo_assignment_time', 'wo_assignment', ['assigned_from', 'assigned_to'])
    
    # 3. purchase_orders - Bestellungen
    op.create_table(
        'purchase_orders',
        sa.Column('id', UUID(as_uuid=True), primary_key=True, server_default=sa.text('gen_random_uuid()')),
        sa.Column('po_number', sa.String(50), unique=True, nullable=False, index=True),
        sa.Column('supplier_id', UUID(as_uuid=True), sa.ForeignKey('suppliers.id'), nullable=False),
        sa.Column('order_date', sa.Date, nullable=False),
        sa.Column('delivery_date', sa.Date),
        sa.Column('status', sa.String(50), server_default='draft', index=True),
        sa.Column('total_amount', sa.Numeric(12, 2)),
        sa.Column('currency', sa.String(3), server_default='EUR'),
        sa.Column('related_wo_id', UUID(as_uuid=True), sa.ForeignKey('workshop_orders.id')),
        sa.Column('notes', sa.Text),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('NOW()')),
        sa.Column('updated_at', sa.DateTime(timezone=True), server_default=sa.text('NOW()'))
    )
    op.create_index('idx_po_supplier', 'purchase_orders', ['supplier_id'])
    op.create_index('idx_po_status', 'purchase_orders', ['status'])
    op.create_index('idx_po_date', 'purchase_orders', ['order_date'])
    
    # 4. purchase_order_lines - Bestellpositionen
    op.create_table(
        'purchase_order_lines',
        sa.Column('id', UUID(as_uuid=True), primary_key=True, server_default=sa.text('gen_random_uuid()')),
        sa.Column('po_id', UUID(as_uuid=True), sa.ForeignKey('purchase_orders.id', ondelete='CASCADE'), nullable=False),
        sa.Column('line_number', sa.Integer, nullable=False),
        sa.Column('part_no', sa.String(100), nullable=False),
        sa.Column('description', sa.Text),
        sa.Column('quantity', sa.Integer, nullable=False),
        sa.Column('unit_price', sa.Numeric(10, 2), nullable=False),
        sa.Column('total_price', sa.Numeric(12, 2), nullable=False),
        sa.Column('received_quantity', sa.Integer, server_default='0'),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('NOW()')),
        sa.Column('updated_at', sa.DateTime(timezone=True), server_default=sa.text('NOW()'))
    )
    op.create_index('idx_po_lines_po', 'purchase_order_lines', ['po_id'])
    op.create_index('idx_po_lines_part', 'purchase_order_lines', ['part_no'])
    
    # 5. invoices - Rechnungen
    op.create_table(
        'invoices',
        sa.Column('id', UUID(as_uuid=True), primary_key=True, server_default=sa.text('gen_random_uuid()')),
        sa.Column('invoice_number', sa.String(50), unique=True, nullable=False, index=True),
        sa.Column('supplier_id', UUID(as_uuid=True), sa.ForeignKey('suppliers.id'), nullable=False),
        sa.Column('invoice_date', sa.Date, nullable=False),
        sa.Column('due_date', sa.Date, nullable=False),
        sa.Column('amount', sa.Numeric(12, 2), nullable=False),
        sa.Column('currency', sa.String(3), server_default='EUR'),
        sa.Column('status', sa.String(50), server_default='pending', index=True),
        sa.Column('related_po_id', UUID(as_uuid=True), sa.ForeignKey('purchase_orders.id')),
        sa.Column('related_wo_id', UUID(as_uuid=True), sa.ForeignKey('workshop_orders.id')),
        sa.Column('cost_center_id', UUID(as_uuid=True)),
        sa.Column('paid_date', sa.Date),
        sa.Column('notes', sa.Text),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('NOW()')),
        sa.Column('updated_at', sa.DateTime(timezone=True), server_default=sa.text('NOW()'))
    )
    op.create_index('idx_invoice_supplier', 'invoices', ['supplier_id'])
    op.create_index('idx_invoice_status', 'invoices', ['status'])
    op.create_index('idx_invoice_date', 'invoices', ['invoice_date'])
    op.create_index('idx_invoice_due', 'invoices', ['due_date'])
    
    # 6. cost_centers - Kostenstellen
    op.create_table(
        'cost_centers',
        sa.Column('id', UUID(as_uuid=True), primary_key=True, server_default=sa.text('gen_random_uuid()')),
        sa.Column('code', sa.String(50), unique=True, nullable=False, index=True),
        sa.Column('name', sa.String(200), nullable=False),
        sa.Column('budget', sa.Numeric(12, 2)),
        sa.Column('spent', sa.Numeric(12, 2), server_default='0'),
        sa.Column('fiscal_year', sa.Integer),
        sa.Column('is_active', sa.Boolean, server_default='true'),
        sa.Column('notes', sa.Text),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('NOW()')),
        sa.Column('updated_at', sa.DateTime(timezone=True), server_default=sa.text('NOW()'))
    )
    op.create_index('idx_cost_center_active', 'cost_centers', ['is_active'])
    op.create_index('idx_cost_center_year', 'cost_centers', ['fiscal_year'])
    
    # Add foreign key to invoices
    op.create_foreign_key('fk_invoice_cost_center', 'invoices', 'cost_centers', ['cost_center_id'], ['id'])
    
    # 7. staff_assignments - Personal-Einsätze
    op.create_table(
        'staff_assignments',
        sa.Column('id', UUID(as_uuid=True), primary_key=True, server_default=sa.text('gen_random_uuid()')),
        sa.Column('staff_id', UUID(as_uuid=True), sa.ForeignKey('staff.id', ondelete='CASCADE'), nullable=False),
        sa.Column('assignment_type', sa.String(50), nullable=False, index=True),
        sa.Column('reference_id', UUID(as_uuid=True)),
        sa.Column('reference_type', sa.String(50)),
        sa.Column('from_datetime', sa.DateTime(timezone=True), nullable=False),
        sa.Column('to_datetime', sa.DateTime(timezone=True), nullable=False),
        sa.Column('status', sa.String(50), server_default='planned'),
        sa.Column('notes', sa.Text),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('NOW()')),
        sa.Column('updated_at', sa.DateTime(timezone=True), server_default=sa.text('NOW()'))
    )
    op.create_index('idx_staff_assign_staff', 'staff_assignments', ['staff_id'])
    op.create_index('idx_staff_assign_type', 'staff_assignments', ['assignment_type'])
    op.create_index('idx_staff_assign_time', 'staff_assignments', ['from_datetime', 'to_datetime'])


def downgrade():
    """Remove Phase 3 tables."""
    op.drop_table('staff_assignments')
    op.drop_foreign_key('fk_invoice_cost_center', 'invoices')
    op.drop_table('cost_centers')
    op.drop_table('invoices')
    op.drop_table('purchase_order_lines')
    op.drop_table('purchase_orders')
    op.drop_table('wo_assignment')
    op.drop_table('tracks')

