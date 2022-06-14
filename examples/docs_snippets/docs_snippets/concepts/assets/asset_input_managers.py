import os

import pandas as pd

from dagster import AssetIn, IOManager, asset, io_manager, with_resources


def store_pandas_dataframe(*_args, **_kwargs):
    pass


def load_pandas_dataframe(*_args, **_kwargs):
    pass


def load_numpy_array(*_args, **_kwargs):
    pass


# start_numpy_example


class PandasAssetIOManager(IOManager):
    def handle_output(self, context, obj):
        file_path = self._get_path(context)
        store_pandas_dataframe(name=file_path, table=obj)

    def _get_path(self, output_context):
        return os.path.join(
            "storage",
            f"{output_context.name}.csv",
        )

    def load_input(self, context):
        file_path = self._get_path(context.upstream_output)
        return load_pandas_dataframe(name=file_path)


@io_manager
def pandas_asset_io_manager():
    return PandasAssetIOManager()


class NumpyAssetIOManager(PandasAssetIOManager):
    def load_input(self, context):
        file_path = self._get_path(context.upstream_output)
        return load_numpy_array(name=file_path)


@io_manager
def numpy_asset_io_manager():
    return NumpyAssetIOManager()


@asset(io_manager_key="pandas_manager")
def upstream_asset():
    return pd.Dataframe([1, 2, 3])


@asset(ins={"upstream": AssetIn(namespace="public", input_manager_key="numpy_manager")})
def downstream_asset(upstream):
    return upstream.shape


assets_with_io_managers = with_resources(
    [upstream_asset, downstream_asset],
    resource_defs={
        "pandas_manager": pandas_asset_io_manager,
        "numpy_manager": numpy_asset_io_manager,
    },
)

# end_numpy_example
