"""initial revision for SQL Server support.

Revision ID: 0e2f5c1b7a94
Revises:
Create Date: 2026-07-29 00:00:00.000000

Deliberately a no-op, mirroring `017_initial_mssql.py`'s counterpart for MySQL in dagster
core.  The three storage classes create their tables with `MetaData.create_all()` and then
stamp this revision, so the schema is never built by migrating up from nothing.  This
revision exists to give the SQL Server tree a head to stamp, and to anchor the revisions
that follow it.

"""

# revision identifiers, used by Alembic.
revision = "0e2f5c1b7a94"
down_revision = None
branch_labels = None
depends_on = None


def upgrade():
    pass


def downgrade():
    pass
