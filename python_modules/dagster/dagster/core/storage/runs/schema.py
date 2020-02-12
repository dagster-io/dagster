import sqlalchemy as db

RunStorageSqlMetadata = db.MetaData()

RunsTable = db.Table(
    'runs',
    RunStorageSqlMetadata,
    db.Column('id', db.Integer, primary_key=True, autoincrement=True),
    db.Column('run_id', db.String(255), unique=True),
    db.Column('pipeline_name', db.String),
    db.Column('status', db.String(63)),
    db.Column('run_body', db.String),
    db.Column('create_timestamp', db.DateTime, server_default=db.text('CURRENT_TIMESTAMP')),
    db.Column('update_timestamp', db.DateTime, server_default=db.text('CURRENT_TIMESTAMP')),
)

RunTagsTable = db.Table(
    'run_tags',
    RunStorageSqlMetadata,
    db.Column('id', db.Integer, primary_key=True, autoincrement=True),
    db.Column('run_id', None, db.ForeignKey('runs.run_id', ondelete="CASCADE")),
    db.Column('key', db.String),
    db.Column('value', db.String),
)
