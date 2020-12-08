from dagster import ModeDefinition, ObjectManager, OutputDefinition, object_manager, pipeline, solid


def connect():
    pass


def write_dataframe_to_table(**_kwargs):
    pass


def read_dataframe_from_table(**_kwargs):
    pass


# solids_start_marker
@solid(output_defs=[OutputDefinition(metadata={"schema": "some_schema", "table": "some_table"})])
def solid1(_):
    """Return a Pandas DataFrame"""


@solid(output_defs=[OutputDefinition(metadata={"schema": "other_schema", "table": "other_table"})])
def solid2(_, _input_dataframe):
    """Return a Pandas DataFrame"""


# solids_end_marker

# asset_store_start_marker
class MyObjectManager(ObjectManager):
    def handle_output(self, context, obj):
        table_name = context.metadata["table"]
        schema = context.metadata["schema"]
        write_dataframe_to_table(name=table_name, schema=schema, dataframe=obj)

    def load_input(self, context):
        table_name = context.upstream_output.metadata["table"]
        schema = context.upstream_output.metadata["schema"]
        return read_dataframe_from_table(name=table_name, schema=schema)


@object_manager
def my_object_manager(_):
    return MyObjectManager()


# asset_store_end_marker


@pipeline(mode_defs=[ModeDefinition(resource_defs={"object_manager": my_object_manager})])
def my_pipeline():
    solid2(solid1())
