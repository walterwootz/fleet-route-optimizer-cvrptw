"""Docs Service Schema - WP5

Revision ID: 003_docs_service
Revises: 002_transfer_hr
Create Date: 2025-11-23 08:45:00

This migration adds ECM-Light document management:
- document_links: Document registry with expiration tracking
- document_versions: Version control for documents
- document_access_log: Append-only audit trail (WORM)
- v_expiring_documents: View for expiration alerts

"""
from alembic import op
import sqlalchemy as sa
from pathlib import Path

# revision identifiers, used by Alembic.
revision = '003_docs_service'
down_revision = '002_transfer_hr'
branch_labels = None
depends_on = None


def upgrade() -> None:
    """Execute Docs Service SQL migration."""

    # Get the base directory (project root)
    base_dir = Path(__file__).parent.parent.parent
    migrations_dir = base_dir / 'src' / 'db' / 'migrations'

    # Execute the SQL file
    sql_file = '08_docs_service.sql'
    file_path = migrations_dir / sql_file

    print(f"Executing {sql_file}...")

    with open(file_path, 'r') as f:
        sql_content = f.read()

    # Execute the SQL
    op.execute(sa.text(sql_content))

    print(f"✓ Completed {sql_file}")


def downgrade() -> None:
    """Downgrade Docs Service schema."""

    # Drop view
    op.execute(sa.text("DROP VIEW IF EXISTS v_expiring_documents CASCADE"))

    # Drop access log rules
    op.execute(sa.text("DROP RULE IF EXISTS document_access_log_no_delete ON document_access_log"))
    op.execute(sa.text("DROP RULE IF EXISTS document_access_log_no_update ON document_access_log"))

    # Drop trigger
    op.execute(sa.text("DROP TRIGGER IF EXISTS update_document_links_updated_at ON document_links"))

    # Drop tables in reverse order
    op.execute(sa.text("DROP TABLE IF EXISTS document_access_log CASCADE"))
    op.execute(sa.text("DROP TABLE IF EXISTS document_versions CASCADE"))
    op.execute(sa.text("DROP TABLE IF EXISTS document_links CASCADE"))

    print("⚠ Docs Service schema downgraded")
