from dagster import (
    op,
    MetadataEntry,
    MetadataValue,
    AssetMaterialization,
    AssetKey
)
from time import time


@op
def does_nothing():
    return None

@op(
    metdata=[
        MetadataEntry.text(label="team", value="core", searchable=True),
        MetadataEntry("")
    ],
)
def op_with_definition_metadata():
    return None


def get_dataframe():
    pass

@op
def op_with_runtime_metadata():
    s = time()
    df = get_dataframe()
    yield AssetMaterialization(
        asset_key=AssetKey("my_table"),
        metadata_entries=[
            MetadataEntry.table_schema(label="my_table_schema", value=df.table_schema, searchable=False)
        ]
    )
    yield MetadataEntry.float(label="duration", value=time() - s)