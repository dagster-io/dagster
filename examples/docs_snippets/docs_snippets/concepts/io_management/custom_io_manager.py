# isort: skip_file
# pylint: disable=reimported
from dagster import job, op


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


# start_io_manager_marker
from dagster import IOManager, io_manager


class MyIOManager(IOManager):
    def _get_path(self, context) -> str:
        return "/".join(context.asset_key.path)

    def handle_output(self, context, obj):
        write_csv(self._get_path(context), obj)

    def load_input(self, context):
        return read_csv(self._get_path(context))


@io_manager
def my_io_manager():
    return MyIOManager()


# end_io_manager_marker


# start_partitioned_marker
class MyPartitionedIOManager(IOManager):
    def _get_path(self, context) -> str:
        if context.has_partition_key:
            return "/".join(context.asset_key.path + [context.asset_partition_key])
        else:
            return "/".join(context.asset_key.path)

    def handle_output(self, context, obj):
        write_csv(self._get_path(context), obj)

    def load_input(self, context):
        return read_csv(self._get_path(context))


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
def df_table_io_manager():
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

        context.add_output_metadata({"num_rows": len(obj), "table_name": table_name})

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
