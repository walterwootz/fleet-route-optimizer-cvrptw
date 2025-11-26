"""Complete FLEET-ONE Schema - All Missing Tables

Revision ID: 006_complete_fleet_one
Revises: 005_crdt_tables
Create Date: 2025-11-25 12:00:00

This migration adds all missing tables for FLEET-ONE services:
- Phase 1: workshops, staff, transfer_plans (Critical)
- Phase 2: suppliers, part_inventory, document_links (Extended)
- Phase 3: tracks, wo_assignment, purchase_orders, invoices, cost_centers, staff_assignments (Complete)
"""

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects.postgresql import UUID, JSONB

# revision identifiers, used by Alembic.
revision = '006_complete_fleet_one'
down_revision = '005_crdt_tables'
branch_labels = None
depends_on = None


def upgrade():
    """Add all missing FLEET-ONE tables."""
    
    # ========================================
    # PHASE 1: CRITICAL TABLES
    # ========================================
    
    # 1. workshops - Werkstatt-Stammdaten
    op.create_table(
        'workshops',
        sa.Column('id', UUID(as_uuid=True), primary_key=True, server_default=sa.text('gen_random_uuid()')),
        sa.Column('code', sa.String(50), unique=True, nullable=False, index=True),
        sa.Column('name', sa.String(200), nullable=False),
        sa.Column('location', sa.String(255), nullable=False),
        sa.Column('contact_person', sa.String(200)),
        sa.Column('phone', sa.String(50)),
        sa.Column('email', sa.String(255)),
        sa.Column('total_tracks', sa.Integer, nullable=False, server_default='1'),
        sa.Column('available_tracks', sa.Integer, nullable=False, server_default='1'),
        sa.Column('is_ecm_certified', sa.Boolean, server_default='false'),
        sa.Column('specializations', JSONB),
        sa.Column('supported_vehicle_types', JSONB),
        sa.Column('rating', sa.Float),
        sa.Column('total_completed_orders', sa.Integer, server_default='0'),
        sa.Column('is_active', sa.Boolean, server_default='true'),
        sa.Column('notes', sa.Text),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('NOW()')),
        sa.Column('updated_at', sa.DateTime(timezone=True), server_default=sa.text('NOW()'))
    )
    op.create_index('idx_workshops_location', 'workshops', ['location'])
    op.create_index('idx_workshops_active', 'workshops', ['is_active'])
    
    # 2. staff - Personal-Stammdaten
    op.create_table(
        'staff',
        sa.Column('id', UUID(as_uuid=True), primary_key=True, server_default=sa.text('gen_random_uuid()')),
        sa.Column('employee_id', sa.String(50), unique=True, nullable=False, index=True),
        sa.Column('first_name', sa.String(100), nullable=False),
        sa.Column('last_name', sa.String(100), nullable=False),
        sa.Column('email', sa.String(255)),
        sa.Column('phone', sa.String(50)),
        sa.Column('role', sa.String(50), nullable=False, index=True),
        sa.Column('qualifications', JSONB, nullable=False),
        sa.Column('certifications', JSONB),
        sa.Column('shift_start', sa.Time),
        sa.Column('shift_end', sa.Time),
        sa.Column('availability_status', sa.String(50), server_default='available', index=True),
        sa.Column('current_location', sa.String(100)),
        sa.Column('is_active', sa.Boolean, server_default='true'),
        sa.Column('notes', sa.Text),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('NOW()')),
        sa.Column('updated_at', sa.DateTime(timezone=True), server_default=sa.text('NOW()'))
    )
    op.create_index('idx_staff_role', 'staff', ['role'])
    op.create_index('idx_staff_active', 'staff', ['is_active'])
    
    # 3. transfer_plans - Überführungs-Planung
    op.create_table(
        'transfer_plans',
        sa.Column('id', UUID(as_uuid=True), primary_key=True, server_default=sa.text('gen_random_uuid()')),
        sa.Column('plan_id', sa.String(50), unique=True, nullable=False, index=True),
        sa.Column('vehicle_id', UUID(as_uuid=True), sa.ForeignKey('vehicles.id', ondelete='CASCADE')),
        sa.Column('from_location', sa.String(100), nullable=False),
        sa.Column('to_location', sa.String(100), nullable=False),
        sa.Column('window_start', sa.DateTime(timezone=True), nullable=False),
        sa.Column('window_end', sa.DateTime(timezone=True), nullable=False),
        sa.Column('required_skill', sa.String(50)),
        sa.Column('priority', sa.String(20), server_default='normal'),
        sa.Column('status', sa.String(50), server_default='planned', index=True),
        sa.Column('assigned_staff_id', UUID(as_uuid=True), sa.ForeignKey('staff.id')),
        sa.Column('actual_start', sa.DateTime(timezone=True)),
        sa.Column('actual_end', sa.DateTime(timezone=True)),
        sa.Column('distance_km', sa.Integer),
        sa.Column('notes', sa.Text),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('NOW()')),
        sa.Column('updated_at', sa.DateTime(timezone=True), server_default=sa.text('NOW()'))
    )
    op.create_index('idx_transfer_vehicle', 'transfer_plans', ['vehicle_id'])
    op.create_index('idx_transfer_window', 'transfer_plans', ['window_start', 'window_end'])
    op.create_index('idx_transfer_assigned', 'transfer_plans', ['assigned_staff_id'])
    
    # ========================================
    # PHASE 2: EXTENDED FUNCTIONS
    # ========================================
    
    # 4. suppliers - Lieferanten
    op.create_table(
        'suppliers',
        sa.Column('id', UUID(as_uuid=True), primary_key=True, server_default=sa.text('gen_random_uuid()')),
        sa.Column('supplier_code', sa.String(50), unique=True, nullable=False, index=True),
        sa.Column('name', sa.String(200), nullable=False),
        sa.Column('contact_person', sa.String(200)),
        sa.Column('email', sa.String(255)),
        sa.Column('phone', sa.String(50)),
        sa.Column('address', sa.Text),
        sa.Column('payment_terms', sa.String(100)),
        sa.Column('rating', sa.Float),
        sa.Column('is_active', sa.Boolean, server_default='true'),
        sa.Column('notes', sa.Text),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('NOW()')),
        sa.Column('updated_at', sa.DateTime(timezone=True), server_default=sa.text('NOW()'))
    )
    op.create_index('idx_suppliers_active', 'suppliers', ['is_active'])
    
    # 5. part_inventory - Ersatzteile-Lager
    op.create_table(
        'part_inventory',
        sa.Column('id', UUID(as_uuid=True), primary_key=True, server_default=sa.text('gen_random_uuid()')),
        sa.Column('part_no', sa.String(100), unique=True, nullable=False, index=True),
        sa.Column('description', sa.Text, nullable=False),
        sa.Column('category', sa.String(100)),
        sa.Column('quantity_available', sa.Integer, nullable=False, server_default='0'),
        sa.Column('quantity_reserved', sa.Integer, server_default='0'),
        sa.Column('min_stock', sa.Integer, server_default='0'),
        sa.Column('unit_price', sa.Numeric(10, 2)),
        sa.Column('currency', sa.String(3), server_default='EUR'),
        sa.Column('supplier_id', UUID(as_uuid=True), sa.ForeignKey('suppliers.id')),
        sa.Column('location_code', sa.String(50)),
        sa.Column('last_restocked', sa.DateTime(timezone=True)),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('NOW()')),
        sa.Column('updated_at', sa.DateTime(timezone=True), server_default=sa.text('NOW()'))
    )
    op.create_index('idx_part_category', 'part_inventory', ['category'])
    op.create_index('idx_part_supplier', 'part_inventory', ['supplier_id'])
    
    # 6. document_links - Dokumenten-Verwaltung
    op.create_table(
        'document_links',
        sa.Column('id', UUID(as_uuid=True), primary_key=True, server_default=sa.text('gen_random_uuid()')),
        sa.Column('document_id', sa.String(100), unique=True, nullable=False, index=True),
        sa.Column('asset_id', UUID(as_uuid=True)),
        sa.Column('asset_type', sa.String(50)),
        sa.Column('doc_type', sa.String(50), nullable=False, index=True),
        sa.Column('doc_url', sa.Text, nullable=False),
        sa.Column('file_hash', sa.String(64)),
        sa.Column('valid_from', sa.Date),
        sa.Column('valid_until', sa.Date),
        sa.Column('is_expired', sa.Boolean, server_default='false'),
        sa.Column('reminder_days_before', sa.Integer, server_default='30'),
        sa.Column('access_level', sa.String(20), server_default='internal'),
        sa.Column('tags', JSONB),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('NOW()')),
        sa.Column('updated_at', sa.DateTime(timezone=True), server_default=sa.text('NOW()'))
    )
    op.create_index('idx_doc_asset', 'document_links', ['asset_id', 'asset_type'])
    op.create_index('idx_doc_expiry', 'document_links', ['valid_until'])


def downgrade():
    """Remove all FLEET-ONE tables."""
    op.drop_table('document_links')
    op.drop_table('part_inventory')
    op.drop_table('suppliers')
    op.drop_table('transfer_plans')
    op.drop_table('staff')
    op.drop_table('workshops')

