"""
Defines a job that computes the weather assets.

Data is locally stored in csv files on the local filesystem.
"""
import os

import pandas as pd
from dagster import AssetKey, IOManager, IOManagerDefinition
from dagster.core.asset_defs import build_assets_job
from pandas import DataFrame

from .assets import daily_temperature_highs, hottest_dates, sfo_q2_weather_sample


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

# build_assets_job_start
weather_job = build_assets_job(
    "weather",
    assets=[daily_temperature_highs, hottest_dates],
    source_assets=[sfo_q2_weather_sample],
    resource_defs={
        "io_manager": IOManagerDefinition.hardcoded_io_manager(LocalFileSystemIOManager())
    },
)
# build_assets_job_end
