'''
This defines a Lakehouse with local storage and Pandas data processing.

Data is locally stored in csv files.

Pandas is used for data processing.  Data can be read from CSV files into a
pandas dataframe, and exported back into pandas dataframes.
'''
import os
from typing import Tuple

import pandas as pd
from lakehouse import AssetStorage, Lakehouse, asset_storage

from dagster import ModeDefinition, StringSource


class LocalFileSystem:
    def __init__(self, config):
        self._root = config['root']

    def get_fs_path(self, path: Tuple[str, ...]) -> str:
        rpath = os.path.join(self._root, *(path[:-1]), path[-1] + '.csv')
        return os.path.abspath(rpath)


@asset_storage(config_schema={'root': StringSource})
def pandas_df_local_filesystem_storage(init_context):
    local_fs = LocalFileSystem(init_context.resource_config)

    class Storage(AssetStorage):
        def save(self, obj: pd.DataFrame, path: Tuple[str, ...], _resources) -> None:
            '''This saves the dataframe as a CSV.'''
            fpath = local_fs.get_fs_path(path)
            obj.to_csv(fpath)

        def load(self, _python_type, path: Tuple[str, ...], _resources):
            '''This reads a dataframe from a CSV.'''
            fpath = local_fs.get_fs_path(path)
            return pd.read_csv(fpath)

    return Storage()


def make_simple_lakehouse():
    dev_mode = ModeDefinition(
        name='dev',
        resource_defs={
            'default_storage': pandas_df_local_filesystem_storage.configured({'root': '.'}),
        },
    )

    return Lakehouse(mode_defs=[dev_mode])


simple_lakehouse = make_simple_lakehouse()
