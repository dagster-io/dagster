"""
This defines a Lakehouse with two options for storage and two options for data-processing.  Both
storage options work with both processing options.

The storage options are local filesystem and S3.  In both cases, data is stored in Parquet files
using the "Hadoop-style" layout in which each table corresponds to a directory, and each file
within the directory contains some of the rows.

The processing options are Pandas and Spark.  A table can be created from a Pandas DataFrame
and then consumed in a downstream computation as a Spark DataFrame.  And vice versa.
"""
import glob
import os
from typing import Tuple

import boto3
import pandas as pd
from dagster import ModeDefinition, StringSource, resource
from dagster_pyspark import pyspark_resource
from lakehouse import AssetStorage, Lakehouse, multi_type_asset_storage
from pandas import DataFrame as PandasDF
from pyspark.sql import DataFrame as SparkDF


class S3:
    def __init__(self, config):
        self._bucket = config["bucket"]
        self._prefix = config["prefix"]

    @property
    def bucket(self):
        return self._bucket

    def get_key(self, path: Tuple[str, ...]):
        return "/".join((self._prefix,) + path)

    def get_path(self, path: Tuple[str, ...]):
        return "/".join((self._bucket, self._prefix) + path)


class LocalFileSystem:
    def __init__(self, config):
        self._root = config["root"]

    def get_fs_path(self, path: Tuple[str, ...]) -> str:
        return os.path.join(self._root, *(path[:-1]), path[-1])


local_filesystem_config_schema = {"root": StringSource}


@resource(config_schema=local_filesystem_config_schema)
def pandas_df_local_filesystem_storage(init_context):
    local_fs = LocalFileSystem(init_context.resource_config)

    class Storage(AssetStorage):
        def save(self, obj: PandasDF, path: Tuple[str, ...], _resources) -> None:
            """This saves the dataframe as a CSV using the layout written and expected by Spark/Hadoop.

            E.g. if the given storage maps the asset's path to the filesystem path "/a/b/c", a directory
            will be created with two files inside it:

                /a/b/c/
                    part-00000.csv
             2       _SUCCESS
            """
            directory = local_fs.get_fs_path(path)
            os.makedirs(directory, exist_ok=True)
            open(os.path.join(directory, "_SUCCESS"), "wb").close()
            csv_path = os.path.join(directory, "part-00000.csv")
            obj.to_csv(csv_path)

        def load(self, _python_type, path: Tuple[str, ...], _resources):
            """This reads a dataframe from a CSV using the layout written and expected by Spark/Hadoop.

            E.g. if the given storage maps the asset's path to the filesystem path "/a/b/c", and that
            directory contains:

                /a/b/c/
                    part-00000.csv
                    part-00001.csv
                    _SUCCESS

            then the produced dataframe will contain the concatenated contents of the two CSV files.
            """
            fs_path = os.path.abspath(local_fs.get_fs_path(path))
            paths = glob.glob(os.path.join(fs_path, "*.csv"))
            if not paths:
                raise FileNotFoundError("No csv files at path {fs_path}".format(fs_path=fs_path))

            return pd.concat(map(pd.read_csv, paths))

    return Storage()


@resource(config_schema=local_filesystem_config_schema)
def spark_df_local_filesystem_storage(init_context):
    local_fs = LocalFileSystem(init_context.resource_config)

    class Storage(AssetStorage):
        def save(self, obj: SparkDF, path: Tuple[str, ...], _resources):
            obj.write.format("csv").options(header="true").save(
                local_fs.get_fs_path(path), mode="overwrite"
            )

        def load(self, _python_type, path, resources):
            return (
                resources.pyspark.spark_session.read.format("csv")
                .options(header="true")
                .load(local_fs.get_fs_path(path))
            )

    return Storage()


s3_config_schema = {"bucket": StringSource, "prefix": StringSource}


@resource(config_schema=s3_config_schema)
def pandas_df_s3_storage(init_context):
    s3 = S3(init_context.resource_config)

    class Storage(AssetStorage):
        def save(self, obj, path, _resources):
            # TODO: write to a temporary file and then boto to s3
            raise NotImplementedError()

        def load(self, _python_type, path, _resources):
            s3_session = boto3.resource("s3")
            s3_obj = s3_session.Object(s3.bucket, s3.get_key(path))  # pylint: disable=no-member
            return pd.read_csv(s3_obj.get()["Body"])

    return Storage()


@resource(config_schema=s3_config_schema)
def spark_df_s3_storage(init_context):
    s3 = S3(init_context.resource_config)

    class Storage(AssetStorage):
        def save(self, obj, path, _resources):
            obj.write.format("csv").options(header="true").save(
                self._get_uri(path), mode="overwrite"
            )

        def load(self, _python_type, path, resources):
            resources.pyspark.spark_session.read.csv(self._get_uri(path))

        def _get_uri(self, path):
            return "s3://" + s3.get_path(path)

    return Storage()


local_file_system_storage = multi_type_asset_storage(
    local_filesystem_config_schema,
    {SparkDF: spark_df_local_filesystem_storage, PandasDF: pandas_df_local_filesystem_storage},
)

s3_storage = multi_type_asset_storage(
    s3_config_schema, {SparkDF: spark_df_s3_storage, PandasDF: pandas_df_s3_storage}
)


def make_simple_lakehouse():
    dev_mode = ModeDefinition(
        name="dev",
        resource_defs={
            "pyspark": pyspark_resource,
            "filesystem": local_file_system_storage.configured({"root": "."}),
        },
    )

    prod_mode = ModeDefinition(
        name="prod",
        resource_defs={
            "pyspark": pyspark_resource,
            "filesystem": s3_storage.configured({"bucket": "some_bucket", "prefix": "some_prefix"}),
        },
    )

    return Lakehouse(
        mode_defs=[dev_mode, prod_mode],
        in_memory_type_resource_keys={SparkDF: ["pyspark"]},
    )


simple_lakehouse = make_simple_lakehouse()
