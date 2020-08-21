import sqlalchemy as db

ScheduleStorageSqlMetadata = db.MetaData()

ScheduleTable = db.Table(
    "schedules",
    ScheduleStorageSqlMetadata,
    db.Column("id", db.Integer, primary_key=True, autoincrement=True),
    db.Column("schedule_origin_id", db.String(255), unique=True),
    db.Column("repository_origin_id", db.String(255)),
    db.Column("status", db.String(63)),
    db.Column("schedule_body", db.String),
    db.Column("create_timestamp", db.DateTime, server_default=db.text("CURRENT_TIMESTAMP")),
    db.Column("update_timestamp", db.DateTime, server_default=db.text("CURRENT_TIMESTAMP")),
)

ScheduleTickTable = db.Table(
    "schedule_ticks",
    ScheduleStorageSqlMetadata,
    db.Column("id", db.Integer, primary_key=True, autoincrement=True),
    db.Column("schedule_origin_id", db.String(255), index=True),
    db.Column("status", db.String(63)),
    db.Column("timestamp", db.types.TIMESTAMP),
    db.Column("tick_body", db.String),
    # The create and update timestamps are not used in framework code, are are simply
    # present for debugging purposes.
    db.Column("create_timestamp", db.DateTime, server_default=db.text("CURRENT_TIMESTAMP")),
    db.Column("update_timestamp", db.DateTime, server_default=db.text("CURRENT_TIMESTAMP")),
)
