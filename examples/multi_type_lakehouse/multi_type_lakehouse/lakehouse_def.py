"""
Defines a job for materializing the airport weather assets.

Data is stored in Parquet files using the "Hadoop-style" layout in which each table corresponds to a
directory, and each file within the directory contains some of the rows.

The processing options are Pandas and Spark.  A table can be created from a Pandas DataFrame
and then consumed in a downstream computation as a Spark DataFrame.  And vice versa.
"""
import glob
import os
from typing import Union

import pandas as pd
from dagster import AssetKey, IOManager, IOManagerDefinition, check
from dagster.core.asset_defs import build_assets_job
from pandas import DataFrame as PandasDF
from pyspark.sql import DataFrame as SparkDF
from pyspark.sql import SparkSession

from .assets import daily_temperature_high_diffs, daily_temperature_highs, sfo_q2_weather_sample


class LocalFileSystemIOManager(IOManager):
    def _get_fs_path(self, asset_key: AssetKey) -> str:
        rpath = os.path.join(asset_key.path) + ".csv"
        return os.path.abspath(rpath)

    def handle_output(self, context, obj: Union[PandasDF, SparkDF]):
        """This saves the dataframe as a CSV using the layout written and expected by Spark/Hadoop.

        E.g. if the given storage maps the asset's path to the filesystem path "/a/b/c", a directory
        will be created with two files inside it:

            /a/b/c/
                part-00000.csv
         2       _SUCCESS
        """
        if isinstance(obj, PandasDF):
            directory = self._get_fs_path(context.asset_key)
            os.makedirs(directory, exist_ok=True)
            open(os.path.join(directory, "_SUCCESS"), "wb").close()
            csv_path = os.path.join(directory, "part-00000.csv")
            obj.to_csv(csv_path)
        elif isinstance(obj, SparkDF):
            obj.write.format("csv").options(header="true").save(
                self._get_fs_path(context.asset_key), mode="overwrite"
            )
        else:
            check.failed("Unexpected object type")

    def load_input(self, context) -> Union[PandasDF, SparkDF]:
        """This reads a dataframe from a CSV using the layout written and expected by Spark/Hadoop.

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
            return pd.concat(map(pd.read_csv, paths))
        elif context.dagster_type.typing_type == SparkDF:
            return (
                SparkSession.builder.getOrCreate()
                .read.format("csv")
                .options(header="true")
                .load(self._get_fs_path(context.asset_key))
            )


airport_weather_job = build_assets_job(
    "airport_weather",
    assets=[daily_temperature_highs, daily_temperature_high_diffs],
    source_assets=[sfo_q2_weather_sample],
    resource_defs={
        "io_manager": IOManagerDefinition.hardcoded_io_manager(LocalFileSystemIOManager())
    },
)
