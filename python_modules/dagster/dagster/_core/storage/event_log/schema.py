import sqlalchemy as db
from sqlalchemy.dialects import sqlite

from ..sql import MySQLCompatabilityTypes, get_current_timestamp

SqlEventLogStorageMetadata = db.MetaData()

SqlEventLogStorageTable = db.Table(
    "event_logs",
    SqlEventLogStorageMetadata,
    db.Column("id", db.Integer, primary_key=True, autoincrement=True),
    db.Column("run_id", db.String(255)),
    db.Column("event", db.Text, nullable=False),
    db.Column("dagster_event_type", db.Text),
    db.Column("timestamp", db.types.TIMESTAMP),
    db.Column("step_key", db.Text),
    db.Column("asset_key", db.Text),
    db.Column("partition", db.Text),
)

SecondaryIndexMigrationTable = db.Table(
    "secondary_indexes",
    SqlEventLogStorageMetadata,
    db.Column("id", db.Integer, primary_key=True, autoincrement=True),
    db.Column("name", MySQLCompatabilityTypes.UniqueText, unique=True),
    db.Column("create_timestamp", db.DateTime, server_default=get_current_timestamp()),
    db.Column("migration_completed", db.DateTime),
)

# The AssetKeyTable contains a `last_materialization_timestamp` column that is exclusively
# used to determine if an asset exists (last materialization timestamp > wipe timestamp).
# This column is used nowhere else, and as of AssetObservation creation, we want to extend
# this functionality to ensure that assets with observation OR materialization timestamp
# > wipe timestamp display in Dagit.

# As of the following PR, we update last_materialization_timestamp to store the timestamp
# of the latest asset observation or materialization that has occurred.
# https://github.com/dagster-io/dagster/pull/6885
AssetKeyTable = db.Table(
    "asset_keys",
    SqlEventLogStorageMetadata,
    db.Column("id", db.Integer, primary_key=True, autoincrement=True),
    db.Column("asset_key", MySQLCompatabilityTypes.UniqueText, unique=True),
    db.Column("last_materialization", db.Text),
    db.Column("last_run_id", db.String(255)),
    db.Column("asset_details", db.Text),
    db.Column("wipe_timestamp", db.types.TIMESTAMP),  # guarded by secondary index check
    # last_materialization_timestamp contains timestamp for latest materialization or observation
    db.Column(
        "last_materialization_timestamp", db.types.TIMESTAMP
    ),  # guarded by secondary index check
    db.Column("tags", db.TEXT),  # guarded by secondary index check
    db.Column("create_timestamp", db.DateTime, server_default=get_current_timestamp()),
    db.Column("cached_status_data", db.TEXT),
)

AssetEventTagsTable = db.Table(
    "asset_event_tags",
    SqlEventLogStorageMetadata,
    db.Column(
        "id",
        db.BigInteger().with_variant(sqlite.INTEGER(), "sqlite"),
        primary_key=True,
        autoincrement=True,
    ),
    db.Column("event_id", db.Integer, db.ForeignKey("event_logs.id", ondelete="CASCADE")),
    db.Column("asset_key", db.Text, nullable=False),
    db.Column("key", db.Text, nullable=False),
    db.Column("value", db.Text),
    db.Column("event_timestamp", db.types.TIMESTAMP),
)

db.Index(
    "idx_step_key",
    SqlEventLogStorageTable.c.step_key,
    mysql_length=32,
)
db.Index(
    "idx_event_type",
    SqlEventLogStorageTable.c.dagster_event_type,
    SqlEventLogStorageTable.c.id,
    mysql_length={"dagster_event_type": 64},
)
db.Index(
    "idx_asset_event_tags",
    AssetEventTagsTable.c.asset_key,
    AssetEventTagsTable.c.key,
    AssetEventTagsTable.c.value,
    mysql_length={"asset_key": 64, "key": 64, "value": 64},
)
db.Index(
    "idx_asset_event_tags_event_id",
    AssetEventTagsTable.c.event_id,
)
db.Index(
    "idx_events_by_run_id",
    SqlEventLogStorageTable.c.run_id,
    SqlEventLogStorageTable.c.id,
    mysql_length={"run_id": 64},
)
db.Index(
    "idx_events_by_asset",
    SqlEventLogStorageTable.c.asset_key,
    SqlEventLogStorageTable.c.dagster_event_type,
    SqlEventLogStorageTable.c.id,
    postgresql_where=(SqlEventLogStorageTable.c.asset_key != None),  # noqa: E711
    mysql_length={"asset_key": 64, "dagster_event_type": 64},
)
db.Index(
    "idx_events_by_asset_partition",
    SqlEventLogStorageTable.c.asset_key,
    SqlEventLogStorageTable.c.dagster_event_type,
    SqlEventLogStorageTable.c.partition,
    SqlEventLogStorageTable.c.id,
    postgresql_where=(
        db.and_(
            SqlEventLogStorageTable.c.asset_key != None,  # noqa: E711
            SqlEventLogStorageTable.c.partition != None,  # noqa: E711
        )
    ),
    mysql_length={"asset_key": 64, "dagster_event_type": 64, "partition": 64},
)
