import os

import pandas as pd
from dagster import AssetKey, IOManager, io_manager


class LocalCsvIOManager(IOManager):
    """Translates between Pandas DataFrames and CSVs on the local filesystem."""

    def __init__(self, base_dir):
        self._base_dir = base_dir

    def _get_fs_path(self, asset_key: AssetKey) -> str:
        rpath = os.path.join(self._base_dir, *asset_key.path) + ".csv"
        return os.path.abspath(rpath)

    def handle_output(self, context, obj: pd.DataFrame):
        """This saves the dataframe as a CSV."""
        fpath = self._get_fs_path(context.asset_key)
        os.makedirs(os.path.dirname(fpath), exist_ok=True)
        obj.to_csv(fpath)

    def load_input(self, context):
        """This reads a dataframe from a CSV."""
        fpath = self._get_fs_path(context.asset_key)
        return pd.read_csv(fpath)


@io_manager
def local_csv_io_manager(context):
    return LocalCsvIOManager(context.instance.storage_directory())
