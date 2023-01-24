import sqlalchemy as db

from ..sql import get_current_timestamp

PartitionsStorageMetadata = db.MetaData()

MutablePartitionsDefinitions = db.Table(
    "mutable_partitions_definitions",
    PartitionsStorageMetadata,
    db.Column("id", db.Integer, primary_key=True, autoincrement=True),
    db.Column("partitions_def_name", db.Text, nullable=False),
    db.Column("partition_key", db.Text, nullable=False),
    db.Column("create_timestamp", db.DateTime, server_default=get_current_timestamp()),
)
