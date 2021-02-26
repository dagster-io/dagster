import sqlalchemy as db

from ..sql import get_current_timestamp

ScheduleStorageSqlMetadata = db.MetaData()

JobTable = db.Table(
    "jobs",
    ScheduleStorageSqlMetadata,
    db.Column("id", db.Integer, primary_key=True, autoincrement=True),
    db.Column("job_origin_id", db.String(255), unique=True),
    db.Column("repository_origin_id", db.String(255)),
    db.Column("status", db.String(63)),
    db.Column("job_type", db.String(63), index=True),
    db.Column("job_body", db.Text),
    db.Column("create_timestamp", db.DateTime, server_default=get_current_timestamp()),
    db.Column("update_timestamp", db.DateTime, server_default=get_current_timestamp()),
)

JobTickTable = db.Table(
    "job_ticks",
    ScheduleStorageSqlMetadata,
    db.Column("id", db.Integer, primary_key=True, autoincrement=True),
    db.Column("job_origin_id", db.String(255), index=True),
    db.Column("status", db.String(63)),
    db.Column("type", db.String(63)),
    db.Column("timestamp", db.types.TIMESTAMP),
    db.Column("tick_body", db.Text),
    db.Column("create_timestamp", db.DateTime, server_default=get_current_timestamp()),
    db.Column("update_timestamp", db.DateTime, server_default=get_current_timestamp()),
)

db.Index("idx_job_tick_status", JobTickTable.c.job_origin_id, JobTickTable.c.status)
db.Index("idx_job_tick_timestamp", JobTickTable.c.job_origin_id, JobTickTable.c.timestamp)
