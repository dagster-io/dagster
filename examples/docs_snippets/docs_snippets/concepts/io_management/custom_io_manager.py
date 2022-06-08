# isort: skip_file
# pylint: disable=reimported
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


def read_csv(_path):
    pass


def write_csv(_path, _obj):
    pass


# start_partitioned_marker
from dagster import IOManager


class MyPartitionedIOManager(IOManager):
    def path_for_partition(self, partition_key):
        return f"some/path/{partition_key}.csv"

    # `context.partition_key` is the run-scoped partition key
    def handle_output(self, context, obj):
        write_csv(self.path_for_partition(context.partition_key), obj)

    # `context.asset_partition_key` is set to the partition key for an asset
    # (if the `IOManager` is handling an asset). This is usually equal to the
    # run `partition_key`.
    def load_input(self, context):
        return read_csv(self.path_for_partition(context.asset_partition_key))


# end_partitioned_marker

# start_df_marker
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


# end_df_marker

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
