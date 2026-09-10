import sqlalchemy as db
from sqlalchemy.dialects import sqlite

from dagster._core.storage.sql import (
    MSSQL_INDEX_KEY_LENGTH,
    MySQLCompatabilityTypes,
    get_sql_current_timestamp,
    mssql_text,
)

ScheduleStorageSqlMetadata = db.MetaData()

JobTable = db.Table(
    "jobs",
    ScheduleStorageSqlMetadata,
    db.Column(
        "id",
        db.BigInteger().with_variant(sqlite.INTEGER(), "sqlite"),
        primary_key=True,
        autoincrement=True,
    ),
    db.Column("job_origin_id", db.String(255), unique=True),
    db.Column("selector_id", db.String(255)),
    db.Column("repository_origin_id", db.String(255)),
    db.Column("status", db.String(63)),
    db.Column("job_type", db.String(63), index=True),
    db.Column("job_body", mssql_text()),
    db.Column("create_timestamp", db.DateTime, server_default=get_sql_current_timestamp()),
    db.Column("update_timestamp", db.DateTime, server_default=get_sql_current_timestamp()),
)

InstigatorsTable = db.Table(
    "instigators",
    ScheduleStorageSqlMetadata,
    db.Column(
        "id",
        db.BigInteger().with_variant(sqlite.INTEGER(), "sqlite"),
        primary_key=True,
        autoincrement=True,
    ),
    db.Column("selector_id", db.String(255), unique=True),
    db.Column("repository_selector_id", db.String(255)),
    db.Column("status", db.String(63)),
    db.Column("instigator_type", db.String(63), index=True),
    db.Column("instigator_body", mssql_text()),
    db.Column("create_timestamp", db.DateTime, server_default=get_sql_current_timestamp()),
    db.Column("update_timestamp", db.DateTime, server_default=get_sql_current_timestamp()),
)

JobTickTable = db.Table(
    "job_ticks",
    ScheduleStorageSqlMetadata,
    db.Column(
        "id",
        db.BigInteger().with_variant(sqlite.INTEGER(), "sqlite"),
        primary_key=True,
        autoincrement=True,
    ),
    db.Column("job_origin_id", db.String(255), index=True),
    db.Column("selector_id", db.String(255)),
    db.Column("status", db.String(63)),
    db.Column("type", db.String(63)),
    db.Column("timestamp", db.types.TIMESTAMP),
    db.Column("tick_body", mssql_text()),
    db.Column("create_timestamp", db.DateTime, server_default=get_sql_current_timestamp()),
    db.Column("update_timestamp", db.DateTime, server_default=get_sql_current_timestamp()),
)

AssetDaemonAssetEvaluationsTable = db.Table(
    "asset_daemon_asset_evaluations",
    ScheduleStorageSqlMetadata,
    db.Column(
        "id",
        db.BigInteger().with_variant(sqlite.INTEGER(), "sqlite"),
        primary_key=True,
        autoincrement=True,
    ),
    db.Column(
        "evaluation_id", db.BigInteger().with_variant(sqlite.INTEGER(), "sqlite"), index=True
    ),
    db.Column("asset_key", mssql_text(MSSQL_INDEX_KEY_LENGTH)),
    db.Column("asset_evaluation_body", mssql_text()),
    db.Column("num_requested", db.Integer),
    db.Column("num_skipped", db.Integer),
    db.Column("num_discarded", db.Integer),
    db.Column("create_timestamp", db.DateTime, server_default=get_sql_current_timestamp()),
)


# Secondary Index migration table, used to track data migrations, event_logs and runs.
# This schema should match the schema in the event_log storage, run schema
SecondaryIndexMigrationTable = db.Table(
    "secondary_indexes",
    ScheduleStorageSqlMetadata,
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

db.Index(
    "idx_job_tick_status",
    JobTickTable.c.job_origin_id,
    JobTickTable.c.status,
    mysql_length=32,
)
db.Index("idx_job_tick_timestamp", JobTickTable.c.job_origin_id, JobTickTable.c.timestamp)
db.Index("idx_tick_selector_timestamp", JobTickTable.c.selector_id, JobTickTable.c.timestamp)

db.Index(
    "idx_asset_daemon_asset_evaluations_asset_key_evaluation_id",
    AssetDaemonAssetEvaluationsTable.c.asset_key,
    AssetDaemonAssetEvaluationsTable.c.evaluation_id,
    # Both columns are nullable, and SQL Server -- unlike everything else -- considers
    # null values equal in a unique index. Filtering them out keeps the behaviour uniform.
    mssql_where=db.and_(
        AssetDaemonAssetEvaluationsTable.c.asset_key != None,  # noqa: E711
        AssetDaemonAssetEvaluationsTable.c.evaluation_id != None,  # noqa: E711
    ),
    mysql_length={"asset_key": 64},
    unique=True,
)
