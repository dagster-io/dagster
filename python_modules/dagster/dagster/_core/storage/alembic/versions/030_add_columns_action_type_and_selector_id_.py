"""add columns action_type and selector_id to bulk_actions.

Revision ID: 6860f830e40c
Revises: 721d858e1dda
Create Date: 2022-05-20 15:00:01.260860

"""
import sqlalchemy as db
from alembic import op
from dagster._core.storage.migration.utils import has_column, has_index, has_table

# revision identifiers, used by Alembic.
revision = "6860f830e40c"
down_revision = "721d858e1dda"
branch_labels = None
depends_on = None


def upgrade():
    if not has_table("bulk_actions"):
        return

    if not has_column("bulk_actions", "action_type"):
        op.add_column("bulk_actions", db.Column("action_type", db.String(32), nullable=True))

    if not has_column("bulk_actions", "selector_id"):
        op.add_column("bulk_actions", db.Column("selector_id", db.Text, nullable=True))

    if not has_index("bulk_actions", "idx_bulk_actions_action_type"):
        op.create_index(
            "idx_bulk_actions_action_type",
            "bulk_actions",
            ["action_type"],
            unique=False,
            mysql_length={"action_type": 32},
        )

    if not has_index("bulk_actions", "idx_bulk_actions_selector_id"):
        op.create_index(
            "idx_bulk_actions_selector_id",
            "bulk_actions",
            ["selector_id"],
            unique=False,
            mysql_length={"selector_id": 64},
        )


def downgrade():
    with op.batch_alter_table("bulk_actions") as batch_op:
        if has_index("bulk_actions", "idx_bulk_actions_action_type"):
            batch_op.drop_index("idx_bulk_actions_action_type")
        if has_index("bulk_actions", "idx_bulk_actions_selector_id"):
            batch_op.drop_index("idx_bulk_actions_selector_id")
        if has_column("bulk_actions", "action_type"):
            batch_op.drop_column("action_type")
        if has_column("bulk_actions", "selector_id"):
            batch_op.drop_column("selector_id")
