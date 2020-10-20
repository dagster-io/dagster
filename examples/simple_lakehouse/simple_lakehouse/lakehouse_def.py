"""
This defines a Lakehouse with local storage and Pandas data processing.

Data is locally stored in csv files.

Pandas is used for data processing.  Data can be read from CSV files into a
pandas dataframe, and exported back into pandas dataframes.
"""
import os
from typing import Tuple

import pandas as pd
from dagster import ModeDefinition, StringSource, resource
from lakehouse import AssetStorage, Lakehouse


class LocalFileSystemStorage(AssetStorage):
    def __init__(self, root):
        self._root = root

    def _get_fs_path(self, path: Tuple[str, ...]) -> str:
        rpath = os.path.join(self._root, *path) + ".csv"
        return os.path.abspath(rpath)

    def save(self, obj: pd.DataFrame, path: Tuple[str, ...], _resources) -> None:
        """This saves the dataframe as a CSV."""
        fpath = self._get_fs_path(path)
        obj.to_csv(fpath)

    def load(self, _python_type, path: Tuple[str, ...], _resources):
        """This reads a dataframe from a CSV."""
        fpath = self._get_fs_path(path)
        return pd.read_csv(fpath)


@resource(config_schema={"root": StringSource})
def local_fs_storage(init_context):
    return LocalFileSystemStorage(init_context.resource_config["root"])


simple_lakehouse = Lakehouse(
    mode_defs=[
        ModeDefinition(
            resource_defs={"default_storage": local_fs_storage.configured({"root": "."})},
        )
    ]
)
