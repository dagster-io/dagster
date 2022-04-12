from time import time

from dagster import AssetKey, AssetMaterialization, MetadataEntry, MetadataValue, job, op

###################


@op
def does_nothing():
    return None


@job(metadata=[MetadataEntry.text(label="team", value="core", searchable=True)])
def job_with_searchable_metadata():
    does_nothing()


###################


@op(
    metdata=[
        MetadataEntry.text(label="team", value="core", searchable=True),
    ],
)
def op_with_definition_metadata():
    return None


###################


def get_dataframe():
    pass


@op
def op_with_runtime_metadata(context):
    s = time()
    df = get_dataframe()
    yield AssetMaterialization(
        asset_key=AssetKey("my_table"),
        metadata=[
            MetadataEntry.table_schema(
                label="my_table_schema", value=df.table_schema, searchable=False
            )
        ],
    )
    yield MetadataEntry.float(label="duration", value=time() - s, searchable=False)
    # or potentially
    context.log_metadata(
        [MetadataEntry.float(label="duration", value=time() - s, searchable=False)]
    )
