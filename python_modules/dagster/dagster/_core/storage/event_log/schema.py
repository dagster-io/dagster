import sqlalchemy as db
from sqlalchemy.dialects import sqlite

from dagster._core.storage.sql import (
    MSSQL_INDEX_KEY_LENGTH,
    MySQLCompatabilityTypes,
    get_sql_current_timestamp,
    mssql_text,
)

SqlEventLogStorageMetadata = db.MetaData()

SqlEventLogStorageTable = db.Table(
    "event_logs",
    SqlEventLogStorageMetadata,
    db.Column(
        "id",
        db.BigInteger().with_variant(sqlite.INTEGER(), "sqlite"),
        primary_key=True,
        autoincrement=True,
    ),
    db.Column("run_id", db.String(255)),
    db.Column("event", MySQLCompatabilityTypes.LongText, nullable=False),
    db.Column("dagster_event_type", mssql_text(64)),
    db.Column("timestamp", db.types.TIMESTAMP),
    db.Column("step_key", mssql_text(128)),
    db.Column("asset_key", mssql_text(MSSQL_INDEX_KEY_LENGTH)),
    db.Column("partition", mssql_text(128)),
)

SecondaryIndexMigrationTable = db.Table(
    "secondary_indexes",
    SqlEventLogStorageMetadata,
    db.Column(
        "id",
        db.BigInteger().with_variant(sqlite.INTEGER(), "sqlite"),
        primary_key=True,
        autoincrement=True,
    ),
    db.Column("name", MySQLCompatabilityTypes.UniqueText, unique=True),
    db.Column("create_timestamp", db.DateTime, server_default=get_sql_current_timestamp()),
    db.Column("migration_completed", db.DateTime),
)

# The AssetKeyTable contains a `last_materialization_timestamp` column that is exclusively
# used to determine if an asset exists (last materialization timestamp > wipe timestamp).
# This column is used nowhere else, and as of AssetObservation creation, we want to extend
# this functionality to ensure that assets with observation OR materialization timestamp
# > wipe timestamp display in the Dagster UI.

# As of the following PR, we update last_materialization_timestamp to store the timestamp
# of the latest asset observation or materialization that has occurred.
# https://github.com/dagster-io/dagster/pull/6885
AssetKeyTable = db.Table(
    "asset_keys",
    SqlEventLogStorageMetadata,
    db.Column(
        "id",
        db.BigInteger().with_variant(sqlite.INTEGER(), "sqlite"),
        primary_key=True,
        autoincrement=True,
    ),
    db.Column("asset_key", MySQLCompatabilityTypes.UniqueText, unique=True),
    db.Column("last_materialization", MySQLCompatabilityTypes.LongText),
    db.Column("last_run_id", db.String(255)),
    db.Column("asset_details", mssql_text()),
    db.Column("wipe_timestamp", db.types.TIMESTAMP),  # guarded by secondary index check
    # last_materialization_timestamp contains timestamp for latest materialization or observation
    db.Column(
        "last_materialization_timestamp", db.types.TIMESTAMP
    ),  # guarded by secondary index check
    db.Column("tags", mssql_text()),  # guarded by secondary index check
    db.Column("create_timestamp", db.DateTime, server_default=get_sql_current_timestamp()),
    db.Column("cached_status_data", MySQLCompatabilityTypes.LongText),
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
    db.Column(
        "event_id",
        db.BigInteger().with_variant(sqlite.INTEGER(), "sqlite"),
    ),
    db.Column("asset_key", mssql_text(MSSQL_INDEX_KEY_LENGTH), nullable=False),
    db.Column("key", mssql_text(128), nullable=False),
    db.Column("value", mssql_text(128)),
    db.Column("event_timestamp", db.types.TIMESTAMP),
)


DynamicPartitionsTable = db.Table(
    "dynamic_partitions",
    SqlEventLogStorageMetadata,
    db.Column(
        "id",
        db.BigInteger().with_variant(sqlite.INTEGER(), "sqlite"),
        primary_key=True,
        autoincrement=True,
    ),
    db.Column("partitions_def_name", mssql_text(128), nullable=False),
    db.Column("partition", mssql_text(128), nullable=False),
    db.Column("create_timestamp", db.DateTime, server_default=get_sql_current_timestamp()),
)

ConcurrencyLimitsTable = db.Table(
    "concurrency_limits",
    SqlEventLogStorageMetadata,
    db.Column(
        "id",
        db.BigInteger().with_variant(sqlite.INTEGER(), "sqlite"),
        primary_key=True,
        autoincrement=True,
    ),
    db.Column("concurrency_key", MySQLCompatabilityTypes.UniqueText, nullable=False, unique=True),
    db.Column("limit", db.Integer, nullable=False),
    db.Column(
        "using_default_limit", db.Boolean, nullable=False, default=False, server_default=db.false()
    ),
    db.Column("update_timestamp", db.DateTime, server_default=get_sql_current_timestamp()),
    db.Column("create_timestamp", db.DateTime, server_default=get_sql_current_timestamp()),
)

ConcurrencySlotsTable = db.Table(
    "concurrency_slots",
    SqlEventLogStorageMetadata,
    db.Column(
        "id",
        db.BigInteger().with_variant(sqlite.INTEGER(), "sqlite"),
        primary_key=True,
        autoincrement=True,
    ),
    db.Column("concurrency_key", mssql_text(255), nullable=False),
    db.Column("run_id", mssql_text(255)),
    db.Column("step_key", mssql_text(128)),
    db.Column("deleted", db.Boolean, nullable=False, default=False),
    db.Column("create_timestamp", db.DateTime, server_default=get_sql_current_timestamp()),
)

PendingStepsTable = db.Table(
    "pending_steps",
    SqlEventLogStorageMetadata,
    db.Column(
        "id",
        db.BigInteger().with_variant(sqlite.INTEGER(), "sqlite"),
        primary_key=True,
        autoincrement=True,
    ),
    db.Column("concurrency_key", mssql_text(255), nullable=False),
    db.Column("run_id", mssql_text(255)),
    db.Column("step_key", mssql_text(128)),
    db.Column("priority", db.Integer),
    db.Column("assigned_timestamp", db.DateTime),
    db.Column("create_timestamp", db.DateTime, server_default=get_sql_current_timestamp()),
)

AssetCheckExecutionsTable = db.Table(
    "asset_check_executions",
    SqlEventLogStorageMetadata,
    db.Column(
        "id",
        db.BigInteger().with_variant(sqlite.INTEGER(), "sqlite"),
        primary_key=True,
        autoincrement=True,
    ),
    db.Column("asset_key", mssql_text(MSSQL_INDEX_KEY_LENGTH)),
    db.Column("check_name", mssql_text(128)),
    db.Column(
        "partition", mssql_text(128)
    ),  # Currently unused. Planned for future partition support
    db.Column("run_id", db.String(255)),
    db.Column("execution_status", db.String(255)),  # Planned, Success, or Failure
    # Either an AssetCheckEvaluationPlanned or AssetCheckEvaluation event
    db.Column("evaluation_event", mssql_text()),
    # Timestamp for an AssetCheckEvaluationPlanned, then replaced by timestamp for the AssetCheckEvaluation event
    db.Column("evaluation_event_timestamp", db.DateTime),
    db.Column(
        "evaluation_event_storage_id",
        db.BigInteger().with_variant(sqlite.INTEGER(), "sqlite"),
    ),
    db.Column(
        "materialization_event_storage_id",
        db.BigInteger().with_variant(sqlite.INTEGER(), "sqlite"),
    ),
    db.Column("create_timestamp", db.DateTime, server_default=get_sql_current_timestamp()),
)

db.Index(
    "idx_asset_check_executions",
    AssetCheckExecutionsTable.c.asset_key,
    AssetCheckExecutionsTable.c.check_name,
    AssetCheckExecutionsTable.c.materialization_event_storage_id,
    AssetCheckExecutionsTable.c.partition,
    mysql_length={
        "asset_key": 64,
        "partition": 64,
        "check_name": 64,
    },
)

# This index doesn't enforce the uniqueness how we want it to because partition and run_id can be
# null. Postgres and other dbms's consider each null value distinct.
#
# SQL Server is the exception: it considers null values *equal* in a unique index, so it
# would allow only one row per (asset_key, check_name) with a null partition and reject the
# rest. Filtering the nulls out of the index reproduces the behaviour of everything else.
db.Index(
    "idx_asset_check_executions_unique",
    AssetCheckExecutionsTable.c.asset_key,
    AssetCheckExecutionsTable.c.check_name,
    AssetCheckExecutionsTable.c.run_id,
    AssetCheckExecutionsTable.c.partition,
    unique=True,
    mssql_where=db.and_(
        AssetCheckExecutionsTable.c.asset_key != None,  # noqa: E711
        AssetCheckExecutionsTable.c.check_name != None,  # noqa: E711
        AssetCheckExecutionsTable.c.run_id != None,  # noqa: E711
        AssetCheckExecutionsTable.c.partition != None,  # noqa: E711
    ),
    mysql_length={"asset_key": 64, "partition": 64, "check_name": 64},
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
    mssql_where=(SqlEventLogStorageTable.c.asset_key != None),  # noqa: E711
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
    mssql_where=(
        db.and_(
            SqlEventLogStorageTable.c.asset_key != None,  # noqa: E711
            SqlEventLogStorageTable.c.partition != None,  # noqa: E711
        )
    ),
    mysql_length={"asset_key": 64, "dagster_event_type": 64, "partition": 64},
)
db.Index(
    "idx_dynamic_partitions",
    DynamicPartitionsTable.c.partitions_def_name,
    DynamicPartitionsTable.c.partition,
    mysql_length={"partitions_def_name": 64, "partition": 64},
    unique=True,
)
db.Index(
    "idx_pending_steps",
    PendingStepsTable.c.concurrency_key,
    PendingStepsTable.c.run_id,
    PendingStepsTable.c.step_key,
    # run_id and step_key are nullable; see idx_asset_check_executions_unique above for
    # why SQL Server needs the nulls filtered out of a unique index.
    mssql_where=db.and_(
        PendingStepsTable.c.run_id != None,  # noqa: E711
        PendingStepsTable.c.step_key != None,  # noqa: E711
    ),
    mysql_length={"concurrency_key": 255, "run_id": 255, "step_key": 32},
    unique=True,
)
