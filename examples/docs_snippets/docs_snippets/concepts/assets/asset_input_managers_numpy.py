from dagster import IOManager, io_manager, AssetIn, asset, with_resources, repository
from .asset_input_managers import (
    store_pandas_dataframe,
    load_pandas_dataframe,
    load_numpy_array,
)
import os
import pandas as pd

# start_numpy_example


class PandasAssetIOManager(IOManager):
    def handle_output(self, context, obj):
        file_path = self._get_path(context)
        store_pandas_dataframe(name=file_path, table=obj)

    def _get_path(self, context):
        return os.path.join(
            "storage",
            f"{context.asset_key.path[-1]}.csv",
        )

    def load_input(self, context):
        file_path = self._get_path(context)
        return load_pandas_dataframe(name=file_path)


@io_manager
def pandas_asset_io_manager():
    return PandasAssetIOManager()


class NumpyAssetIOManager(PandasAssetIOManager):
    def load_input(self, context):
        file_path = self._get_path(context)
        return load_numpy_array(name=file_path)


@io_manager
def numpy_asset_io_manager():
    return NumpyAssetIOManager()


@asset(io_manager_key="pandas_manager")
def upstream_asset():
    return pd.DataFrame([1, 2, 3])


@asset(
    ins={"upstream": AssetIn(key_prefix="public", input_manager_key="numpy_manager")}
)
def downstream_asset(upstream):
    return upstream.shape


@repository
def my_repository():
    return [
        *with_resources(
            [upstream_asset, downstream_asset],
            resource_defs={
                "pandas_manager": pandas_asset_io_manager,
                "numpy_manager": numpy_asset_io_manager,
            },
        )
    ]


# end_numpy_example
