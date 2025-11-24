"""Event Sourcing Schema - WP15 (Phase 3)

Revision ID: 004_event_sourcing
Revises: 003_docs_service
Create Date: 2025-11-24 10:00:00

This migration adds Event Sourcing infrastructure:
- events: Append-only event store with JSONB data
- event_snapshots: Aggregate snapshots for performance
- Indexes for efficient event queries

"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql
from datetime import datetime

# revision identifiers, used by Alembic.
revision = '004_event_sourcing'
down_revision = '003_docs_service'
branch_labels = None
depends_on = None


def upgrade() -> None:
    """Create event sourcing tables."""

    # Create events table
    op.create_table(
        'events',
        sa.Column('event_id', sa.String(), nullable=False),
        sa.Column('event_type', sa.String(), nullable=False),
        sa.Column('event_version', sa.Integer(), nullable=False, server_default='1'),
        sa.Column('aggregate_id', sa.String(), nullable=False),
        sa.Column('aggregate_type', sa.String(), nullable=False),
        sa.Column('aggregate_version', sa.Integer(), nullable=False),
        sa.Column('occurred_at', sa.DateTime(), nullable=False),
        sa.Column('created_at', sa.DateTime(), nullable=False, server_default=sa.text('CURRENT_TIMESTAMP')),
        sa.Column('data', postgresql.JSONB(), nullable=False, server_default='{}'),
        sa.Column('metadata', postgresql.JSONB(), nullable=False, server_default='{}'),
        sa.PrimaryKeyConstraint('event_id')
    )

    # Create indexes for events table
    op.create_index('ix_events_event_type', 'events', ['event_type'])
    op.create_index('ix_events_aggregate_id', 'events', ['aggregate_id'])
    op.create_index('ix_events_aggregate_type', 'events', ['aggregate_type'])
    op.create_index('ix_events_occurred_at', 'events', ['occurred_at'])
    op.create_index(
        'ix_events_aggregate_version',
        'events',
        ['aggregate_id', 'aggregate_version'],
        unique=True
    )
    op.create_index(
        'ix_events_aggregate_type_time',
        'events',
        ['aggregate_type', 'occurred_at']
    )
    op.create_index(
        'ix_events_event_type_time',
        'events',
        ['event_type', 'occurred_at']
    )
    op.create_index(
        'ix_events_aggregate_id_version',
        'events',
        ['aggregate_id', 'aggregate_version']
    )

    # Create event_snapshots table
    op.create_table(
        'event_snapshots',
        sa.Column('snapshot_id', sa.String(), nullable=False),
        sa.Column('aggregate_id', sa.String(), nullable=False),
        sa.Column('aggregate_type', sa.String(), nullable=False),
        sa.Column('aggregate_version', sa.Integer(), nullable=False),
        sa.Column('state', postgresql.JSONB(), nullable=False),
        sa.Column('created_at', sa.DateTime(), nullable=False, server_default=sa.text('CURRENT_TIMESTAMP')),
        sa.PrimaryKeyConstraint('snapshot_id')
    )

    # Create indexes for event_snapshots table
    op.create_index('ix_snapshots_aggregate_id', 'event_snapshots', ['aggregate_id'])
    op.create_index('ix_snapshots_aggregate_type', 'event_snapshots', ['aggregate_type'])
    op.create_index(
        'ix_snapshots_aggregate_version',
        'event_snapshots',
        ['aggregate_id', 'aggregate_version']
    )
    op.create_index(
        'ix_snapshots_aggregate_type_created',
        'event_snapshots',
        ['aggregate_type', 'created_at']
    )

    print("✓ Created event sourcing tables (events, event_snapshots)")


def downgrade() -> None:
    """Drop event sourcing tables."""

    # Drop indexes
    op.drop_index('ix_snapshots_aggregate_type_created', table_name='event_snapshots')
    op.drop_index('ix_snapshots_aggregate_version', table_name='event_snapshots')
    op.drop_index('ix_snapshots_aggregate_type', table_name='event_snapshots')
    op.drop_index('ix_snapshots_aggregate_id', table_name='event_snapshots')

    op.drop_index('ix_events_aggregate_id_version', table_name='events')
    op.drop_index('ix_events_event_type_time', table_name='events')
    op.drop_index('ix_events_aggregate_type_time', table_name='events')
    op.drop_index('ix_events_aggregate_version', table_name='events')
    op.drop_index('ix_events_occurred_at', table_name='events')
    op.drop_index('ix_events_aggregate_type', table_name='events')
    op.drop_index('ix_events_aggregate_id', table_name='events')
    op.drop_index('ix_events_event_type', table_name='events')

    # Drop tables
    op.drop_table('event_snapshots')
    op.drop_table('events')

    print("✓ Dropped event sourcing tables")
