# local_spark_filesystem_io_manager.py

# Data is stored in Parquet files using the "Hadoop-style" layout in which each table corresponds to a
# directory, and each file within the directory contains some of the rows.

# The processing options are Pandas and Spark. A table can be created from a Pandas DataFrame
# and then consumed in a downstream computation as a Spark DataFrame, and vice versa.

import glob
import os
from typing import Union

import pandas as pd
from dagster import (
    AssetKey,
    ConfigurableIOManager,
    _check as check,
)
from pandas import DataFrame as PandasDF
from pyspark.sql import (
    DataFrame as SparkDF,
    SparkSession,
)


class LocalFileSystemIOManager(ConfigurableIOManager):
    def _get_fs_path(self, asset_key: AssetKey) -> str:
        return os.path.abspath(os.path.join(*asset_key.path))

    def handle_output(self, context, obj: Union[PandasDF, SparkDF]):
        """This saves the DataFrame as a CSV using the layout written and expected by Spark/Hadoop.

        E.g. if the given storage maps the asset's path to the filesystem path "/a/b/c", a directory
        will be created with two files inside it:

            /a/b/c/
                part-00000.csv
         2       _SUCCESS
        """
        if isinstance(obj, PandasDF):
            directory = self._get_fs_path(context.asset_key)
            os.makedirs(directory, exist_ok=True)
            csv_path = os.path.join(directory, "part-00000.csv")
            obj.to_csv(csv_path)
            open(os.path.join(directory, "_SUCCESS"), "wb").close()
        elif isinstance(obj, SparkDF):
            obj.write.format("csv").options(header="true").save(
                self._get_fs_path(context.asset_key), mode="overwrite"
            )
        else:
            raise ValueError("Unexpected input type")

    def load_input(self, context) -> Union[PandasDF, SparkDF]:
        """This reads a DataFrame from a CSV using the layout written and expected by Spark/Hadoop.

        E.g. if the given storage maps the asset's path to the filesystem path "/a/b/c", and that
        directory contains:

            /a/b/c/
                part-00000.csv
                part-00001.csv
                _SUCCESS

        then the produced dataframe will contain the concatenated contents of the two CSV files.
        """
        if context.dagster_type.typing_type == PandasDF:
            fs_path = os.path.abspath(self._get_fs_path(context.asset_key))
            paths = glob.glob(os.path.join(fs_path, "*.csv"))
            check.invariant(len(paths) > 0, f"No csv files found under {fs_path}")
            return pd.concat(map(pd.read_csv, paths))
        elif context.dagster_type.typing_type == SparkDF:
            return (
                SparkSession.builder.getOrCreate()  # type: ignore
                .read.format("csv")
                .options(header="true")
                .load(self._get_fs_path(context.asset_key))
            )
        else:
            raise ValueError("Unexpected input type")
