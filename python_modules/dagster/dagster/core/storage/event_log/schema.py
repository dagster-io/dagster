import sqlalchemy as db

SqlEventLogStorageMetadata = db.MetaData()

SqlEventLogStorageTable = db.Table(
    'event_logs',
    SqlEventLogStorageMetadata,
    db.Column('id', db.Integer, primary_key=True, autoincrement=True),
    db.Column('run_id', db.String(255)),
    db.Column('event', db.Text, nullable=False),
    db.Column('dagster_event_type', db.Text),
    db.Column('timestamp', db.types.TIMESTAMP),
)
