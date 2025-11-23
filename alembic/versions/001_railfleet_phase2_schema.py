"""RailFleet Phase 2 Schema - WP3

Revision ID: 001_railfleet_phase2
Revises:
Create Date: 2025-11-23 08:15:00

This migration executes the Phase 2 SQL schema files in order:
- 01_work_orders.sql: Extends work_orders with scheduler fields
- 02_resources.sql: Tracks, teams, and availability windows
- 03_parts.sql: Parts inventory and consumption tracking
- 04_assignments.sql: Solver solutions and work order assignments
- 05_event_log_conflicts.sql: Event log (WORM), sync conflicts, audit log
- 06_kpi_views.sql: Reporting views for dashboards

"""
from alembic import op
import sqlalchemy as sa
from pathlib import Path

# revision identifiers, used by Alembic.
revision = '001_railfleet_phase2'
down_revision = None
branch_labels = None
depends_on = None


def upgrade() -> None:
    """Execute all Phase 2 SQL migration files in order."""

    # Get the base directory (project root)
    base_dir = Path(__file__).parent.parent.parent
    migrations_dir = base_dir / 'src' / 'db' / 'migrations'

    # SQL files to execute in order
    sql_files = [
        '01_work_orders.sql',
        '02_resources.sql',
        '03_parts.sql',
        '04_assignments.sql',
        '05_event_log_conflicts.sql',
        '06_kpi_views.sql',
    ]

    # Execute each SQL file
    for sql_file in sql_files:
        file_path = migrations_dir / sql_file
        print(f"Executing {sql_file}...")

        with open(file_path, 'r') as f:
            sql_content = f.read()

        # Execute the SQL - op.execute handles multi-statement SQL
        op.execute(sa.text(sql_content))

        print(f"✓ Completed {sql_file}")


def downgrade() -> None:
    """Downgrade Phase 2 schema.

    Note: Some tables (event_log, audit_log) are append-only with RULES
    preventing UPDATE/DELETE. Downgrade will drop tables but cannot recover data.
    """

    # Drop views (in reverse order)
    op.execute(sa.text("DROP VIEW IF EXISTS v_solver_metrics CASCADE"))
    op.execute(sa.text("DROP VIEW IF EXISTS v_maintenance_backlog CASCADE"))
    op.execute(sa.text("DROP VIEW IF EXISTS v_parts_usage_summary CASCADE"))
    op.execute(sa.text("DROP VIEW IF EXISTS v_vehicle_availability CASCADE"))
    op.execute(sa.text("DROP VIEW IF EXISTS v_on_time_performance CASCADE"))
    op.execute(sa.text("DROP VIEW IF EXISTS v_track_utilization CASCADE"))

    # Drop tables from 05_event_log_conflicts.sql
    op.execute(sa.text("DROP RULE IF EXISTS audit_log_no_delete ON audit_log"))
    op.execute(sa.text("DROP RULE IF EXISTS audit_log_no_update ON audit_log"))
    op.execute(sa.text("DROP TABLE IF EXISTS audit_log CASCADE"))
    op.execute(sa.text("DROP TABLE IF EXISTS sync_conflicts CASCADE"))
    op.execute(sa.text("DROP RULE IF EXISTS event_log_no_delete ON event_log"))
    op.execute(sa.text("DROP RULE IF EXISTS event_log_no_update ON event_log"))
    op.execute(sa.text("DROP TABLE IF EXISTS event_log CASCADE"))

    # Drop tables from 04_assignments.sql
    op.execute(sa.text("DROP TABLE IF EXISTS solver_solutions CASCADE"))
    op.execute(sa.text("DROP TABLE IF EXISTS wo_assignment CASCADE"))

    # Drop tables from 03_parts.sql
    op.execute(sa.text("DROP TRIGGER IF EXISTS used_parts_decrement_stock ON used_parts"))
    op.execute(sa.text("DROP FUNCTION IF EXISTS decrement_part_stock()"))
    op.execute(sa.text("DROP TABLE IF EXISTS used_parts CASCADE"))
    op.execute(sa.text("DROP TABLE IF EXISTS part_availability CASCADE"))
    op.execute(sa.text("DROP TABLE IF EXISTS part_inventory CASCADE"))

    # Drop tables from 02_resources.sql
    op.execute(sa.text("DROP TRIGGER IF EXISTS update_teams_updated_at ON teams"))
    op.execute(sa.text("DROP TRIGGER IF EXISTS update_tracks_updated_at ON tracks"))
    op.execute(sa.text("DROP TABLE IF EXISTS team_availability CASCADE"))
    op.execute(sa.text("DROP TABLE IF EXISTS teams CASCADE"))
    op.execute(sa.text("DROP TABLE IF EXISTS track_availability CASCADE"))
    op.execute(sa.text("DROP TABLE IF EXISTS tracks CASCADE"))
    op.execute(sa.text("DROP FUNCTION IF EXISTS update_updated_at_column()"))

    # Revert 01_work_orders.sql changes
    op.execute(sa.text("""
        ALTER TABLE work_orders
        DROP COLUMN IF EXISTS incompatible_assets,
        DROP COLUMN IF EXISTS hard_deadline_ts,
        DROP COLUMN IF EXISTS latest_end_ts,
        DROP COLUMN IF EXISTS earliest_start_ts,
        DROP COLUMN IF EXISTS required_parts,
        DROP COLUMN IF EXISTS required_skills,
        DROP COLUMN IF EXISTS duration_min
    """))

    print("⚠ Phase 2 schema downgraded - data in append-only tables is lost")
