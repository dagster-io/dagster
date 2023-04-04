"""An asset with associated `TableMetadataValue` and `TableSchemaMetadataValue.

The asset does nothing. It exists just to have a place to attach the TableMetadataValue.
"""

from dagster import MetadataValue, asset
from dagster._core.definitions.metadata.table import (
    TableColumn,
    TableColumnConstraints,
    TableRecord,
    TableSchema,
)

table_metadata = MetadataValue.table(
    records=[
        TableRecord(dict(name="Alice", age=30, height=172.5, is_resident=True)),
        TableRecord(dict(name="Bob", age=52, height=183.8, is_resident=False)),
        TableRecord(dict(name="Candace", age=77, height=169.0, is_resident=False)),
    ],
    schema=TableSchema(
        columns=[
            TableColumn("name", "string", description="The name of the person"),
            TableColumn(
                "age",
                "int",
                description="The age of the person",
                constraints=TableColumnConstraints(nullable=False, other=[">0"]),
            ),
            TableColumn(
                "height",
                "float",
                description="The height of the person in centimeters",
                constraints=TableColumnConstraints(nullable=False, other=[">0"]),
            ),
            TableColumn(
                "is_resident", "bool", description="Whether the person is a resident of the city"
            ),
        ]
    ),
)


@asset(metadata={"resident_info": table_metadata})
def alpha():
    return 1
