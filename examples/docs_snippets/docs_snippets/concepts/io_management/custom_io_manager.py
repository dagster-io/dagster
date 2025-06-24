# ruff: isort: skip_file
import dagster as dg


@dg.op
def op_1():
    return []


@dg.op
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
import dagster as dg


class MyIOManager(dg.ConfigurableIOManager):
    # specifies an optional string list input, via config system
    path_prefix: list[str] = []

    def _get_path(self, context) -> str:
        return "/".join(self.path_prefix + context.asset_key.path)

    def handle_output(self, context: dg.OutputContext, obj):
        write_csv(self._get_path(context), obj)

    def load_input(self, context: dg.InputContext):
        return read_csv(self._get_path(context))


# end_io_manager_marker

# start_io_manager_factory_marker
import dagster as dg


class ExternalIOManager(dg.IOManager):
    def __init__(self, api_token):
        self._api_token = api_token
        # setup stateful cache
        self._cache = {}

    def handle_output(self, context: dg.OutputContext, obj): ...

    def load_input(self, context: dg.InputContext):
        if context.asset_key in self._cache:
            return self._cache[context.asset_key]
        ...


class ConfigurableExternalIOManager(dg.ConfigurableIOManagerFactory):
    api_token: str

    def create_io_manager(self, context) -> ExternalIOManager:
        return ExternalIOManager(self.api_token)


# end_io_manager_factory_marker


# start_partitioned_marker
class MyPartitionedIOManager(dg.IOManager):
    def _get_path(self, context) -> str:
        if context.has_partition_key:
            return "/".join(context.asset_key.path + [context.asset_partition_key])
        else:
            return "/".join(context.asset_key.path)

    def handle_output(self, context: dg.OutputContext, obj):
        write_csv(self._get_path(context), obj)

    def load_input(self, context: dg.InputContext):
        return read_csv(self._get_path(context))


# end_partitioned_marker

# start_df_marker
from dagster import ConfigurableIOManager


class DataframeTableIOManager(dg.ConfigurableIOManager):
    def handle_output(self, context: dg.OutputContext, obj):
        # name is the name given to the Out that we're storing for
        table_name = context.name
        write_dataframe_to_table(name=table_name, dataframe=obj)

    def load_input(self, context: dg.InputContext):
        # upstream_output.name is the name given to the Out that we're loading for
        if context.upstream_output:
            table_name = context.upstream_output.name
            return read_dataframe_from_table(name=table_name)


@dg.job(resource_defs={"io_manager": DataframeTableIOManager()})
def my_job():
    op_2(op_1())


# end_df_marker


# start_metadata_marker
class DataframeTableIOManagerWithMetadata(dg.ConfigurableIOManager):
    def handle_output(self, context: dg.OutputContext, obj):
        table_name = context.name
        write_dataframe_to_table(name=table_name, dataframe=obj)

        context.add_output_metadata({"num_rows": len(obj), "table_name": table_name})

    def load_input(self, context: dg.InputContext):
        if context.upstream_output:
            table_name = context.upstream_output.name
            return read_dataframe_from_table(name=table_name)


# end_metadata_marker


@dg.job(resource_defs={"io_manager": DataframeTableIOManagerWithMetadata()})
def my_job_with_metadata():
    op_2(op_1())
