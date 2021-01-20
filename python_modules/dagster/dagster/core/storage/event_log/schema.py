import sqlalchemy as db

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
    db.Column("name", db.Text, unique=True),
    db.Column("create_timestamp", db.DateTime, server_default=db.text("CURRENT_TIMESTAMP")),
    db.Column("migration_completed", db.DateTime),
)

AssetKeyTable = db.Table(
    "asset_keys",
    SqlEventLogStorageMetadata,
    db.Column("id", db.Integer, primary_key=True, autoincrement=True),
    db.Column("asset_key", db.Text, unique=True),
    db.Column("create_timestamp", db.DateTime, server_default=db.text("CURRENT_TIMESTAMP")),
)

db.Index("idx_run_id", SqlEventLogStorageTable.c.run_id)
db.Index("idx_step_key", SqlEventLogStorageTable.c.step_key)
db.Index("idx_asset_key", SqlEventLogStorageTable.c.asset_key)
db.Index(
    "idx_asset_partition", SqlEventLogStorageTable.c.asset_key, SqlEventLogStorageTable.c.partition
)
