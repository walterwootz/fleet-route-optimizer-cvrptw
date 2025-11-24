"""Sync device tables for local-first synchronization

Revision ID: 006
Revises: 005
Create Date: 2025-01-24 14:00:00.000000

"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects.postgresql import JSONB

# revision identifiers, used by Alembic.
revision = '006'
down_revision = '005'
branch_labels = None
depends_on = None


def upgrade() -> None:
    """Create sync device and session tables."""

    # Create sync_devices table
    op.create_table(
        'sync_devices',
        sa.Column('id', sa.Integer(), autoincrement=True, nullable=False),
        sa.Column('device_id', sa.String(), nullable=False),
        sa.Column('device_name', sa.String(), nullable=False),
        sa.Column('device_type', sa.String(), nullable=False),
        sa.Column('platform', sa.String(), nullable=True),
        sa.Column('app_version', sa.String(), nullable=True),
        sa.Column('last_ip_address', sa.String(), nullable=True),
        sa.Column('last_sync_at', sa.DateTime(), nullable=True),
        sa.Column('last_push_at', sa.DateTime(), nullable=True),
        sa.Column('last_pull_at', sa.DateTime(), nullable=True),
        sa.Column('is_active', sa.Boolean(), nullable=False, server_default='true'),
        sa.Column('is_offline', sa.Boolean(), nullable=False, server_default='false'),
        sa.Column('capabilities', JSONB, nullable=False, server_default='{}'),
        sa.Column('user_id', sa.Integer(), nullable=True),
        sa.Column('registered_at', sa.DateTime(), nullable=False, server_default=sa.text('CURRENT_TIMESTAMP')),
        sa.Column('updated_at', sa.DateTime(), nullable=False, server_default=sa.text('CURRENT_TIMESTAMP')),
        sa.PrimaryKeyConstraint('id'),
        sa.UniqueConstraint('device_id')
    )

    # Create indexes for sync_devices
    op.create_index('ix_sync_devices_device_id', 'sync_devices', ['device_id'], unique=True)
    op.create_index('ix_sync_devices_device_type', 'sync_devices', ['device_type'])
    op.create_index('ix_sync_devices_is_active', 'sync_devices', ['is_active'])
    op.create_index('ix_sync_devices_last_sync', 'sync_devices', ['last_sync_at'])
    op.create_index('ix_sync_devices_user', 'sync_devices', ['user_id'])

    # Create sync_sessions table
    op.create_table(
        'sync_sessions',
        sa.Column('id', sa.Integer(), autoincrement=True, nullable=False),
        sa.Column('session_id', sa.String(), nullable=False),
        sa.Column('device_id', sa.String(), nullable=False),
        sa.Column('sync_type', sa.String(), nullable=False),
        sa.Column('entities_synced', sa.Integer(), nullable=False, server_default='0'),
        sa.Column('conflicts_resolved', sa.Integer(), nullable=False, server_default='0'),
        sa.Column('operations_applied', sa.Integer(), nullable=False, server_default='0'),
        sa.Column('tombstones_processed', sa.Integer(), nullable=False, server_default='0'),
        sa.Column('errors_count', sa.Integer(), nullable=False, server_default='0'),
        sa.Column('session_data', JSONB, nullable=False, server_default='{}'),
        sa.Column('errors', JSONB, nullable=False, server_default='[]'),
        sa.Column('started_at', sa.DateTime(), nullable=False, server_default=sa.text('CURRENT_TIMESTAMP')),
        sa.Column('completed_at', sa.DateTime(), nullable=True),
        sa.Column('status', sa.String(), nullable=False, server_default="'in_progress'"),
        sa.PrimaryKeyConstraint('id'),
        sa.UniqueConstraint('session_id')
    )

    # Create indexes for sync_sessions
    op.create_index('ix_sync_sessions_session_id', 'sync_sessions', ['session_id'], unique=True)
    op.create_index('ix_sync_sessions_device_id', 'sync_sessions', ['device_id'])
    op.create_index('ix_sync_sessions_started_at', 'sync_sessions', ['started_at'])
    op.create_index('ix_sync_sessions_device_started', 'sync_sessions', ['device_id', 'started_at'])
    op.create_index('ix_sync_sessions_status', 'sync_sessions', ['status'])
    op.create_index('ix_sync_sessions_type', 'sync_sessions', ['sync_type'])


def downgrade() -> None:
    """Drop sync tables."""

    # Drop indexes for sync_sessions
    op.drop_index('ix_sync_sessions_type', table_name='sync_sessions')
    op.drop_index('ix_sync_sessions_status', table_name='sync_sessions')
    op.drop_index('ix_sync_sessions_device_started', table_name='sync_sessions')
    op.drop_index('ix_sync_sessions_started_at', table_name='sync_sessions')
    op.drop_index('ix_sync_sessions_device_id', table_name='sync_sessions')
    op.drop_index('ix_sync_sessions_session_id', table_name='sync_sessions')

    # Drop sync_sessions table
    op.drop_table('sync_sessions')

    # Drop indexes for sync_devices
    op.drop_index('ix_sync_devices_user', table_name='sync_devices')
    op.drop_index('ix_sync_devices_last_sync', table_name='sync_devices')
    op.drop_index('ix_sync_devices_is_active', table_name='sync_devices')
    op.drop_index('ix_sync_devices_device_type', table_name='sync_devices')
    op.drop_index('ix_sync_devices_device_id', table_name='sync_devices')

    # Drop sync_devices table
    op.drop_table('sync_devices')
