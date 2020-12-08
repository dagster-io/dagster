from dagster import AssetStore, ModeDefinition, OutputDefinition, pipeline, resource, solid


def connect():
    pass


def write_dataframe_to_table(**_kwargs):
    pass


def read_dataframe_from_table(**_kwargs):
    pass


# solids_start_marker
@solid(
    output_defs=[OutputDefinition(asset_metadata={"schema": "some_schema", "table": "some_table"})]
)
def solid1(_):
    """Return a Pandas DataFrame"""


@solid(
    output_defs=[
        OutputDefinition(asset_metadata={"schema": "other_schema", "table": "other_table"})
    ]
)
def solid2(_, _input_dataframe):
    """Return a Pandas DataFrame"""


# solids_end_marker

# asset_store_start_marker
class MyAssetStore(AssetStore):
    def set_asset(self, context, obj):
        table_name = context.asset_metadata["table"]
        schema = context.asset_metadata["schema"]
        write_dataframe_to_table(name=table_name, schema=schema, dataframe=obj)

    def get_asset(self, context):
        table_name = context.asset_metadata["table"]
        schema = context.asset_metadata["schema"]
        return read_dataframe_from_table(name=table_name, schema=schema)


@resource
def my_asset_store(_):
    return MyAssetStore()


# asset_store_end_marker


@pipeline(mode_defs=[ModeDefinition(resource_defs={"object_manager": my_asset_store})])
def my_pipeline():
    solid2(solid1())
