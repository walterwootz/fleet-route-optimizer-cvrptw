"""CRDT tables for conflict-free synchronization

Revision ID: 005
Revises: 004
Create Date: 2025-01-24 12:00:00.000000

"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects.postgresql import JSONB

# revision identifiers, used by Alembic.
revision = '005'
down_revision = '004'
branch_labels = None
depends_on = None


def upgrade() -> None:
    """Create CRDT metadata and operations tables."""

    # Create crdt_metadata table
    op.create_table(
        'crdt_metadata',
        sa.Column('id', sa.Integer(), autoincrement=True, nullable=False),
        sa.Column('entity_type', sa.String(), nullable=False),
        sa.Column('entity_id', sa.String(), nullable=False),
        sa.Column('device_id', sa.String(), nullable=False),
        sa.Column('vector_clock', JSONB, nullable=False, server_default='{}'),
        sa.Column('crdt_data', JSONB, nullable=False, server_default='{}'),
        sa.Column('tombstone', sa.Boolean(), nullable=False, server_default='false'),
        sa.Column('created_at', sa.DateTime(), nullable=False, server_default=sa.text('CURRENT_TIMESTAMP')),
        sa.Column('updated_at', sa.DateTime(), nullable=False, server_default=sa.text('CURRENT_TIMESTAMP')),
        sa.PrimaryKeyConstraint('id')
    )

    # Create indexes for crdt_metadata
    op.create_index('ix_crdt_metadata_entity_type', 'crdt_metadata', ['entity_type'])
    op.create_index('ix_crdt_metadata_entity_id', 'crdt_metadata', ['entity_id'])
    op.create_index('ix_crdt_metadata_device_id', 'crdt_metadata', ['device_id'])
    op.create_index('ix_crdt_entity', 'crdt_metadata', ['entity_type', 'entity_id', 'device_id'])
    op.create_index('ix_crdt_device_updated', 'crdt_metadata', ['device_id', 'updated_at'])
    op.create_index('ix_crdt_active', 'crdt_metadata', ['entity_type', 'tombstone', 'updated_at'])

    # Create crdt_operations table
    op.create_table(
        'crdt_operations',
        sa.Column('id', sa.Integer(), autoincrement=True, nullable=False),
        sa.Column('operation_id', sa.String(), nullable=False),
        sa.Column('entity_type', sa.String(), nullable=False),
        sa.Column('entity_id', sa.String(), nullable=False),
        sa.Column('device_id', sa.String(), nullable=False),
        sa.Column('operation_type', sa.String(), nullable=False),
        sa.Column('operation_data', JSONB, nullable=False, server_default='{}'),
        sa.Column('vector_clock', JSONB, nullable=False, server_default='{}'),
        sa.Column('created_at', sa.DateTime(), nullable=False, server_default=sa.text('CURRENT_TIMESTAMP')),
        sa.PrimaryKeyConstraint('id'),
        sa.UniqueConstraint('operation_id')
    )

    # Create indexes for crdt_operations
    op.create_index('ix_crdt_operations_operation_id', 'crdt_operations', ['operation_id'], unique=True)
    op.create_index('ix_crdt_operations_entity_type', 'crdt_operations', ['entity_type'])
    op.create_index('ix_crdt_operations_entity_id', 'crdt_operations', ['entity_id'])
    op.create_index('ix_crdt_operations_device_id', 'crdt_operations', ['device_id'])
    op.create_index('ix_crdt_operations_created_at', 'crdt_operations', ['created_at'])
    op.create_index('ix_crdt_ops_entity', 'crdt_operations', ['entity_type', 'entity_id', 'created_at'])
    op.create_index('ix_crdt_ops_device', 'crdt_operations', ['device_id', 'created_at'])


def downgrade() -> None:
    """Drop CRDT tables."""

    # Drop indexes for crdt_operations
    op.drop_index('ix_crdt_ops_device', table_name='crdt_operations')
    op.drop_index('ix_crdt_ops_entity', table_name='crdt_operations')
    op.drop_index('ix_crdt_operations_created_at', table_name='crdt_operations')
    op.drop_index('ix_crdt_operations_device_id', table_name='crdt_operations')
    op.drop_index('ix_crdt_operations_entity_id', table_name='crdt_operations')
    op.drop_index('ix_crdt_operations_entity_type', table_name='crdt_operations')
    op.drop_index('ix_crdt_operations_operation_id', table_name='crdt_operations')

    # Drop crdt_operations table
    op.drop_table('crdt_operations')

    # Drop indexes for crdt_metadata
    op.drop_index('ix_crdt_active', table_name='crdt_metadata')
    op.drop_index('ix_crdt_device_updated', table_name='crdt_metadata')
    op.drop_index('ix_crdt_entity', table_name='crdt_metadata')
    op.drop_index('ix_crdt_metadata_device_id', table_name='crdt_metadata')
    op.drop_index('ix_crdt_metadata_entity_id', table_name='crdt_metadata')
    op.drop_index('ix_crdt_metadata_entity_type', table_name='crdt_metadata')

    # Drop crdt_metadata table
    op.drop_table('crdt_metadata')
