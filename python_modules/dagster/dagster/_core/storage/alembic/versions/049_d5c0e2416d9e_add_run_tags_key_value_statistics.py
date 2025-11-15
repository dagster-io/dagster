"""add run_tags key value statistics

Revision ID: d5c0e2416d9e
Revises: 7e2f3204cf8e
Create Date: 2025-11-15 23:13:08.062589

"""

from alembic import op

# revision identifiers, used by Alembic.
revision = "d5c0e2416d9e"
down_revision = "7e2f3204cf8e"
branch_labels = None
depends_on = None


def upgrade():
    bind = op.get_bind()
    # Only postgresql supports cross column statistics
    if bind.dialect.name == "postgresql":
        # Add correlation statistics on key, value
        op.execute(
            "CREATE STATISTICS run_tags_key_value_stats (dependencies, ndistinct) ON key, value FROM run_tags;"
        )
        # Increase number of samples (run_tags can be a huge table)
        op.execute("ALTER TABLE run_tags ALTER COLUMN value SET STATISTICS 500;")
        # Update statistics
        op.execute("ANALYZE run_tags")


def downgrade():
    bind = op.get_bind()
    if bind.dialect.name == "postgresql":
        # Remove correlation statistics on key, value
        op.execute("DROP STATISTICS run_tags_key_value_stats;")
        # Reset to default
        op.execute("ALTER TABLE run_tags ALTER COLUMN value SET STATISTICS -1;")
