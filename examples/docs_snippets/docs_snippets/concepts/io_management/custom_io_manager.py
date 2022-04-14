# isort: skip_file
from dagster import job, op, MetadataEntry


@op
def op_1():
    return []


@op
def op_2(_a):
    return []


def write_dataframe_to_table(**_kwargs):
    pass


def read_dataframe_from_table(**_kwargs):
    return []


# start_marker
from dagster import IOManager, io_manager


class DataframeTableIOManager(IOManager):
    def handle_output(self, context, obj):
        # name is the name given to the Out that we're storing for
        table_name = context.name
        write_dataframe_to_table(name=table_name, dataframe=obj)

    def load_input(self, context):
        # upstream_output.name is the name given to the Out that we're loading for
        table_name = context.upstream_output.name
        return read_dataframe_from_table(name=table_name)


@io_manager
def df_table_io_manager(_):
    return DataframeTableIOManager()


@job(resource_defs={"io_manager": df_table_io_manager})
def my_job():
    op_2(op_1())


# end_marker

# start_metadata_marker
class DataframeTableIOManagerWithMetadata(IOManager):
    def handle_output(self, context, obj):
        table_name = context.name
        write_dataframe_to_table(name=table_name, dataframe=obj)

        # attach these to the Handled Output event
        yield MetadataEntry.int(len(obj), label="number of rows")
        yield MetadataEntry.text(table_name, label="table name")

    def load_input(self, context):
        table_name = context.upstream_output.name
        return read_dataframe_from_table(name=table_name)


# end_metadata_marker


@io_manager
def df_table_io_manager_with_metadata(_):
    return DataframeTableIOManagerWithMetadata()


@job(resource_defs={"io_manager": df_table_io_manager_with_metadata})
def my_job_with_metadata():
    op_2(op_1())
