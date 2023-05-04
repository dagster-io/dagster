"""add postgres pks

Revision ID: 701913684cb4
Revises: d9092588866f
Create Date: 2023-05-04 09:12:34.974039

"""
from alembic import op
from dagster._core.storage.migration.utils import get_primary_key, has_column, has_table

# revision identifiers, used by Alembic.
revision = "701913684cb4"
down_revision = "d9092588866f"
branch_labels = None
depends_on = None


def has_primary_key(tablename):
    primary_key = get_primary_key(tablename)
    return primary_key and len(primary_key.get("constrained_columns", [])) > 0


def upgrade():
    if has_table("kvs") and has_column("kvs", "id") and not has_primary_key("kvs"):
        op.create_primary_key("kvs_pkey", "kvs", ["id"])

    if (
        has_table("instance_info")
        and has_column("instance_info", "id")
        and not has_primary_key("instance_info")
    ):
        op.create_primary_key("instance_info_pkey", "instance_info", ["id"])

    if (
        has_table("daemon_heartbeats")
        and has_column("daemon_heartbeats", "id")
        and not has_primary_key("daemon_heartbeats")
    ):
        op.create_primary_key("daemon_heartbeats_pkey", "daemon_heartbeats", ["id"])


def downgrade():
    pass
