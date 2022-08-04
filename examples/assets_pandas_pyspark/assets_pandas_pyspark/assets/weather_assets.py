"""isort:skip_file

Defines a group of weather assets.

Data is locally stored in csv files on the local filesystem.
"""
import os

import pandas as pd
from pandas import DataFrame

from dagster import AssetKey, IOManager, IOManagerDefinition

# io_manager_start
class LocalFileSystemIOManager(IOManager):
    """Translates between Pandas DataFrames and CSVs on the local filesystem."""

    def _get_fs_path(self, asset_key: AssetKey) -> str:
        rpath = os.path.join(*asset_key.path) + ".csv"
        return os.path.abspath(rpath)

    def handle_output(self, context, obj: DataFrame):
        """This saves the dataframe as a CSV."""
        fpath = self._get_fs_path(context.asset_key)
        obj.to_csv(fpath)

    def load_input(self, context):
        """This reads a dataframe from a CSV."""
        fpath = self._get_fs_path(context.asset_key)
        return pd.read_csv(fpath)


# io_manager_end

# gather_assets_start
# imports the module called "assets" from the package containing the current module
# the "assets" module contains the asset definitions
from . import table_assets
from dagster import load_assets_from_modules, with_resources

weather_assets = with_resources(
    load_assets_from_modules(modules=[table_assets]),
    resource_defs={
        "io_manager": IOManagerDefinition.hardcoded_io_manager(LocalFileSystemIOManager())
    },
)

# gather_assets_end
