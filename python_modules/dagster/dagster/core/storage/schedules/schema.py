import sqlalchemy as db

from ..sql import MySQLCompatabilityTypes, get_current_timestamp

ScheduleStorageSqlMetadata = db.MetaData()

JobTable = db.Table(
    "jobs",
    ScheduleStorageSqlMetadata,
    db.Column("id", db.Integer, primary_key=True, autoincrement=True),
    db.Column("job_origin_id", db.String(255), unique=True),
    db.Column("selector_id", db.String(255)),
    db.Column("repository_origin_id", db.String(255)),
    db.Column("status", db.String(63)),
    db.Column("job_type", db.String(63), index=True),
    db.Column("job_body", db.Text),
    db.Column("create_timestamp", db.DateTime, server_default=get_current_timestamp()),
    db.Column("update_timestamp", db.DateTime, server_default=get_current_timestamp()),
)

InstigatorsTable = db.Table(
    "instigators",
    ScheduleStorageSqlMetadata,
    db.Column("id", db.Integer, primary_key=True, autoincrement=True),
    db.Column("selector_id", db.String(255), unique=True),
    db.Column("repository_selector_id", db.String(255)),
    db.Column("status", db.String(63)),
    db.Column("instigator_type", db.String(63), index=True),
    db.Column("instigator_body", db.Text),
    db.Column("create_timestamp", db.DateTime, server_default=get_current_timestamp()),
    db.Column("update_timestamp", db.DateTime, server_default=get_current_timestamp()),
)

JobTickTable = db.Table(
    "job_ticks",
    ScheduleStorageSqlMetadata,
    db.Column("id", db.Integer, primary_key=True, autoincrement=True),
    db.Column("job_origin_id", db.String(255), index=True),
    db.Column("selector_id", db.String(255)),
    db.Column("status", db.String(63)),
    db.Column("type", db.String(63)),
    db.Column("timestamp", db.types.TIMESTAMP),
    db.Column("tick_body", db.Text),
    db.Column("create_timestamp", db.DateTime, server_default=get_current_timestamp()),
    db.Column("update_timestamp", db.DateTime, server_default=get_current_timestamp()),
)

# Secondary Index migration table, used to track data migrations, event_logs and runs.
# This schema should match the schema in the event_log storage, run schema
SecondaryIndexMigrationTable = db.Table(
    "secondary_indexes",
    ScheduleStorageSqlMetadata,
    db.Column("id", db.Integer, primary_key=True, autoincrement=True),
    db.Column("name", MySQLCompatabilityTypes.UniqueText, unique=True),
    db.Column("create_timestamp", db.DateTime, server_default=get_current_timestamp()),
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
