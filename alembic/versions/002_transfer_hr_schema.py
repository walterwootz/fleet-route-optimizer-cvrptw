"""Transfer and HR Services Schema - WP4

Revision ID: 002_transfer_hr
Revises: 001_railfleet_phase2
Create Date: 2025-11-23 08:30:00

This migration adds Transfer and HR service tables:
- transfer_plans: Locomotive movement/transfer planning
- transfer_assignments: Vehicle-to-plan assignments
- staff: Personnel management (drivers, mechanics, technicians)
- staff_assignments: Staff assignments to work orders/transfers

"""
from alembic import op
import sqlalchemy as sa
from pathlib import Path

# revision identifiers, used by Alembic.
revision = '002_transfer_hr'
down_revision = '001_railfleet_phase2'
branch_labels = None
depends_on = None


def upgrade() -> None:
    """Execute Transfer & HR SQL migration."""

    # Get the base directory (project root)
    base_dir = Path(__file__).parent.parent.parent
    migrations_dir = base_dir / 'src' / 'db' / 'migrations'

    # Execute the SQL file
    sql_file = '07_transfer_hr.sql'
    file_path = migrations_dir / sql_file

    print(f"Executing {sql_file}...")

    with open(file_path, 'r') as f:
        sql_content = f.read()

    # Execute the SQL
    op.execute(sa.text(sql_content))

    print(f"✓ Completed {sql_file}")


def downgrade() -> None:
    """Downgrade Transfer & HR schema."""

    # Drop tables in reverse order
    op.execute(sa.text("DROP TRIGGER IF EXISTS update_staff_updated_at ON staff"))
    op.execute(sa.text("DROP TRIGGER IF EXISTS update_transfer_plans_updated_at ON transfer_plans"))

    op.execute(sa.text("DROP TABLE IF EXISTS staff_assignments CASCADE"))
    op.execute(sa.text("DROP TABLE IF EXISTS staff CASCADE"))
    op.execute(sa.text("DROP TABLE IF EXISTS transfer_assignments CASCADE"))
    op.execute(sa.text("DROP TABLE IF EXISTS transfer_plans CASCADE"))

    print("⚠ Transfer & HR schema downgraded")
