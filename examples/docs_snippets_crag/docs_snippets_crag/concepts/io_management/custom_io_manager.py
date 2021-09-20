"""isort:skip_file"""
from dagster import solid, EventMetadataEntry


@solid
def solid1():
    return []


@solid
def solid2(_a):
    return []


def write_dataframe_to_table(**_kwargs):
    pass


def read_dataframe_from_table(**_kwargs):
    return []


# start_marker
from dagster import IOManager, ModeDefinition, io_manager, pipeline


class DataframeTableIOManager(IOManager):
    def handle_output(self, context, obj):
        # name is the name given to the OutputDefinition that we're storing for
        table_name = context.name
        write_dataframe_to_table(name=table_name, dataframe=obj)

    def load_input(self, context):
        # upstream_output.name is the name given to the OutputDefinition that we're loading for
        table_name = context.upstream_output.name
        return read_dataframe_from_table(name=table_name)


@io_manager
def df_table_io_manager(_):
    return DataframeTableIOManager()


@pipeline(mode_defs=[ModeDefinition(resource_defs={"io_manager": df_table_io_manager})])
def my_pipeline():
    solid2(solid1())


# end_marker

# start_metadata_marker
class DataframeTableIOManagerWithMetadata(IOManager):
    def handle_output(self, context, obj):
        table_name = context.name
        write_dataframe_to_table(name=table_name, dataframe=obj)

        # attach these to the Handled Output event
        yield EventMetadataEntry.int(len(obj), label="number of rows")
        yield EventMetadataEntry.text(table_name, label="table name")

    def load_input(self, context):
        table_name = context.upstream_output.name
        return read_dataframe_from_table(name=table_name)


# end_metadata_marker


@io_manager
def df_table_io_manager_with_metadata(_):
    return DataframeTableIOManagerWithMetadata()


@pipeline(
    mode_defs=[ModeDefinition(resource_defs={"io_manager": df_table_io_manager_with_metadata})]
)
def my_pipeline_with_metadata():
    solid2(solid1())
