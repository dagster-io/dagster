"""add asset check and asset check partition tables

Revision ID: 6636a21bc6c7
Revises: 7e2f3204cf8e
Create Date: 2025-09-03 10:38:41.994954

"""

import sqlalchemy as db
from alembic import op
from dagster._core.storage.migration.utils import has_index, has_table
from dagster._core.storage.sql import get_sql_current_timestamp
from sqlalchemy.dialects import sqlite

# revision identifiers, used by Alembic.
revision = "6636a21bc6c7"
down_revision = "7e2f3204cf8e"
branch_labels = None
depends_on = None


def upgrade():
    # Create asset_checks table (registry of all asset checks)
    if not has_table("asset_checks"):
        op.create_table(
            "asset_checks",
            db.Column(
                "id",
                db.BigInteger().with_variant(sqlite.INTEGER(), "sqlite"),
                primary_key=True,
                autoincrement=True,
            ),
            db.Column("asset_key", db.Text, nullable=False),
            db.Column("check_name", db.Text, nullable=False),
            db.Column(
                "cached_check_status_data", db.Text
            ),  # Serialized AssetCheckPartitionStatusCacheValue
            db.Column(
                "subset_cache_event_id",
                db.BigInteger().with_variant(sqlite.INTEGER(), "sqlite"),
            ),  # Event ID when subset cache was last updated
            # Summary data for efficient AssetCheckSummaryRecord creation
            db.Column(
                "last_execution_record_id",
                db.BigInteger().with_variant(sqlite.INTEGER(), "sqlite"),
            ),  # Reference to latest asset_check_executions.id
            db.Column("last_run_id", db.String(255)),  # Run ID of latest execution
            db.Column(
                "last_completed_execution_record_id",
                db.BigInteger().with_variant(sqlite.INTEGER(), "sqlite"),
            ),  # Reference to latest completed asset_check_executions.id
            db.Column("created_timestamp", db.DateTime, server_default=get_sql_current_timestamp()),
            db.Column("updated_timestamp", db.DateTime),
        )

    # Create asset_check_partitions table (partition-level status tracking)
    if not has_table("asset_check_partitions"):
        op.create_table(
            "asset_check_partitions",
            db.Column(
                "id",
                db.BigInteger().with_variant(sqlite.INTEGER(), "sqlite"),
                primary_key=True,
                autoincrement=True,
            ),
            db.Column("asset_key", db.Text, nullable=False),
            db.Column("check_name", db.Text, nullable=False),
            db.Column("partition_key", db.Text),  # NULL for non-partitioned checks
            db.Column("last_execution_status", db.Text),
            # Reference to asset_check_executions.id for detailed execution record
            db.Column(
                "last_execution_id",
                db.BigInteger().with_variant(sqlite.INTEGER(), "sqlite"),
            ),
            db.Column("last_execution_timestamp", db.DateTime),
            # Run ID when this partition was planned (for resolving planned -> in_progress/skipped/failed)
            db.Column("last_planned_run_id", db.String(255)),
            # Event log entry ID when this partition row was last updated (for cache invalidation)
            db.Column(
                "last_event_id",
                db.BigInteger().with_variant(sqlite.INTEGER(), "sqlite"),
                nullable=False,
            ),
            db.Column("created_timestamp", db.DateTime, server_default=get_sql_current_timestamp()),
            db.Column("updated_timestamp", db.DateTime),
        )

    # Create unique index on asset_checks for uniqueness constraint (MySQL compatible)
    if not has_index("asset_checks", "idx_asset_checks_unique"):
        op.create_index(
            "idx_asset_checks_unique",
            "asset_checks",
            ["asset_key", "check_name"],
            mysql_length={"asset_key": 64, "check_name": 64},
            unique=True,
        )

    # Create index on asset_checks table for efficient asset-level queries
    if not has_index("asset_checks", "idx_asset_checks"):
        op.create_index(
            "idx_asset_checks",
            "asset_checks",
            ["asset_key"],
            mysql_length={"asset_key": 64},
        )

    # Create unique index on asset_check_partitions for uniqueness constraint (MySQL compatible)
    if not has_index("asset_check_partitions", "idx_asset_check_partitions_unique"):
        op.create_index(
            "idx_asset_check_partitions_unique",
            "asset_check_partitions",
            ["asset_key", "check_name", "partition_key"],
            mysql_length={"asset_key": 64, "check_name": 64, "partition_key": 64},
            unique=True,
        )

    # Create index on asset_check_partitions for efficient check-level queries
    if not has_index("asset_check_partitions", "idx_asset_check_partitions"):
        op.create_index(
            "idx_asset_check_partitions",
            "asset_check_partitions",
            ["asset_key", "check_name"],
            mysql_length={"asset_key": 64, "check_name": 64},
        )

    # Create index for cache invalidation queries (find partitions newer than cache)
    if not has_index("asset_check_partitions", "idx_asset_check_partitions_cache"):
        op.create_index(
            "idx_asset_check_partitions_cache",
            "asset_check_partitions",
            ["asset_key", "check_name", "last_event_id"],
            mysql_length={"asset_key": 64, "check_name": 64},
        )


def downgrade():
    # Drop indexes first (reverse order of creation)
    if has_index("asset_check_partitions", "idx_asset_check_partitions_cache"):
        op.drop_index("idx_asset_check_partitions_cache", "asset_check_partitions")

    if has_index("asset_check_partitions", "idx_asset_check_partitions"):
        op.drop_index("idx_asset_check_partitions", "asset_check_partitions")

    if has_index("asset_check_partitions", "idx_asset_check_partitions_unique"):
        op.drop_index("idx_asset_check_partitions_unique", "asset_check_partitions")

    if has_index("asset_checks", "idx_asset_checks"):
        op.drop_index("idx_asset_checks", "asset_checks")

    if has_index("asset_checks", "idx_asset_checks_unique"):
        op.drop_index("idx_asset_checks_unique", "asset_checks")

    if has_table("asset_check_partitions"):
        op.drop_table("asset_check_partitions")

    if has_table("asset_checks"):
        op.drop_table("asset_checks")
