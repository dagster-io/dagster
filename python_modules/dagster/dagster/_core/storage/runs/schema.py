import sqlalchemy as db
from sqlalchemy.dialects import sqlite

from ..sql import MySQLCompatabilityTypes, get_current_timestamp

RunStorageSqlMetadata = db.MetaData()

RunsTable = db.Table(
    "runs",
    RunStorageSqlMetadata,
    db.Column("id", db.Integer, primary_key=True, autoincrement=True),
    db.Column("run_id", db.String(255), unique=True),
    db.Column(
        "snapshot_id",
        db.String(255),
        db.ForeignKey("snapshots.snapshot_id", name="fk_runs_snapshot_id_snapshots_snapshot_id"),
    ),
    db.Column("pipeline_name", db.Text),
    db.Column(
        "mode", db.Text
    ),  # The mode column may be filled with garbage data. In 0.13.0, it is no longer populated.
    db.Column("status", db.String(63)),
    db.Column("run_body", db.Text),
    db.Column("partition", db.Text),
    db.Column("partition_set", db.Text),
    db.Column("create_timestamp", db.DateTime, server_default=get_current_timestamp()),
    db.Column("update_timestamp", db.DateTime, server_default=get_current_timestamp()),
    # Added start/end_time in #6038 (12/2021), MySQL fix added in #6451 (2/2022)
    # We are using floats here to store unix timestamps in the database. They are optional perf
    # optimizations, mirroring the timestamps in the event_log for the corresponding events marking
    # the start and end of the run.  Using the float datatype is a bit of a hack - we had to change
    # the underlying datatype in MySQL to avoid timestamp truncation.  Ideally, we could use a
    # Timestamp field or Datetime field, but we lack the appropriate handling in the application
    # layer to deal with the timezone-offsets at the insertion/fetching boundary with some DBs
    # (notably Postgres DBs with a non-UTC timezone set).  This isn't a problem for the existing
    # DateTime / Timestamp fields used in the rest of the codebase, because those fields are only
    # used for query filtering, not for actual display in the UI (they instead use the float values
    # within a JSON-serialized payload). We may want to revisit this in the future, dropping these
    # columns in favor of DateTime / Timestamp columns.
    db.Column("start_time", db.Float),
    db.Column("end_time", db.Float),
)

# Secondary Index migration table, used to track data migrations, both for event_logs and runs.
# This schema should match the schema in the event_log storage schema
SecondaryIndexMigrationTable = db.Table(
    "secondary_indexes",
    RunStorageSqlMetadata,
    db.Column("id", db.Integer, primary_key=True, autoincrement=True),
    db.Column("name", MySQLCompatabilityTypes.UniqueText, unique=True),
    db.Column("create_timestamp", db.DateTime, server_default=get_current_timestamp()),
    db.Column("migration_completed", db.DateTime),
)

RunTagsTable = db.Table(
    "run_tags",
    RunStorageSqlMetadata,
    db.Column("id", db.Integer, primary_key=True, autoincrement=True),
    db.Column("run_id", None, db.ForeignKey("runs.run_id", ondelete="CASCADE")),
    db.Column("key", db.Text),
    db.Column("value", db.Text),
)

SnapshotsTable = db.Table(
    "snapshots",
    RunStorageSqlMetadata,
    db.Column("id", db.Integer, primary_key=True, autoincrement=True, nullable=False),
    db.Column("snapshot_id", db.String(255), unique=True, nullable=False),
    db.Column("snapshot_body", db.LargeBinary, nullable=False),
    db.Column("snapshot_type", db.String(63), nullable=False),
)

DaemonHeartbeatsTable = db.Table(
    "daemon_heartbeats",
    RunStorageSqlMetadata,
    db.Column(
        "id",
        db.BigInteger().with_variant(sqlite.INTEGER(), "sqlite"),
        primary_key=True,
        autoincrement=True,
    ),
    db.Column("daemon_type", db.String(255), unique=True, nullable=False),
    db.Column("daemon_id", db.String(255)),
    db.Column("timestamp", db.types.TIMESTAMP, nullable=False),
    db.Column("body", db.Text),  # serialized DaemonHeartbeat
)

BulkActionsTable = db.Table(
    "bulk_actions",
    RunStorageSqlMetadata,
    db.Column("id", db.Integer, primary_key=True, autoincrement=True),
    db.Column("key", db.String(32), unique=True, nullable=False),
    db.Column("status", db.String(255), nullable=False),
    db.Column("timestamp", db.types.TIMESTAMP, nullable=False),
    db.Column("body", db.Text),
    db.Column("action_type", db.String(32)),
    db.Column("selector_id", db.Text),
)

InstanceInfo = db.Table(
    "instance_info",
    RunStorageSqlMetadata,
    db.Column(
        "id",
        db.BigInteger().with_variant(sqlite.INTEGER(), "sqlite"),
        primary_key=True,
        autoincrement=True,
    ),
    db.Column("run_storage_id", db.Text),
)

KeyValueStoreTable = db.Table(
    "kvs",
    RunStorageSqlMetadata,
    db.Column(
        "id",
        db.BigInteger().with_variant(sqlite.INTEGER(), "sqlite"),
        primary_key=True,
        autoincrement=True,
    ),
    db.Column("key", db.Text, nullable=False),
    db.Column("value", db.Text),
)

db.Index("idx_run_tags", RunTagsTable.c.key, RunTagsTable.c.value, mysql_length=64)
db.Index("idx_run_partitions", RunsTable.c.partition_set, RunsTable.c.partition, mysql_length=64)
db.Index(
    "idx_runs_by_job",
    RunsTable.c.pipeline_name,
    RunsTable.c.id,
    mysql_length={
        "pipeline_name": 255,
    },
)
db.Index("idx_bulk_actions", BulkActionsTable.c.key, mysql_length=32)
db.Index("idx_bulk_actions_status", BulkActionsTable.c.status, mysql_length=32)
db.Index("idx_bulk_actions_action_type", BulkActionsTable.c.action_type, mysql_length=32)
db.Index("idx_bulk_actions_selector_id", BulkActionsTable.c.selector_id, mysql_length=64)
db.Index("idx_run_status", RunsTable.c.status, mysql_length=32)
db.Index(
    "idx_run_range",
    RunsTable.c.status,
    RunsTable.c.update_timestamp,
    RunsTable.c.create_timestamp,
    mysql_length={
        "status": 32,
        "update_timestamp": 8,
        "create_timestamp": 8,
    },
)
db.Index("idx_kvs_keys_unique", KeyValueStoreTable.c.key, unique=True, mysql_length=64)
