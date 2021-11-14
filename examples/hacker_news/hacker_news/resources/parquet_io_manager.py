import os
from typing import Union

import pandas
import pyspark
from dagster import AssetKey, EventMetadataEntry, Field, IOManager, OutputContext, check, io_manager
from dagster.seven.temp_dir import get_system_temp_directory
from hacker_news.partitions import hourly_partitions


class PartitionedParquetIOManager(IOManager):
    """
    This IOManager will take in a pandas or pyspark dataframe and store it in parquet at the
    specified path.

    It stores outputs for different partitions in different filepaths.

    Downstream ops can either load this dataframe into a spark session or simply retrieve a path
    to where the data is stored.
    """

    def __init__(self, base_path):
        self._base_path = base_path

    def handle_output(
        self, context: OutputContext, obj: Union[pandas.DataFrame, pyspark.sql.DataFrame]
    ):

        path = self._get_path(context)
        if isinstance(obj, pandas.DataFrame):
            row_count = len(obj)
            obj.to_parquet(path=path, index=False)
        elif isinstance(obj, pyspark.sql.DataFrame):
            row_count = obj.count()
            obj.write.parquet(path=path, mode="overwrite")
        else:
            raise Exception(f"Outputs of type {type(obj)} not supported.")
        yield EventMetadataEntry.int(value=row_count, label="row_count")
        yield EventMetadataEntry.path(path=path, label="path")

    def load_input(self, context) -> Union[pyspark.sql.DataFrame, str]:
        # In this load_input function, we vary the behavior based on the type of the downstream input
        path = self._get_path(context.upstream_output)
        if context.dagster_type.typing_type == pyspark.sql.DataFrame:
            # return pyspark dataframe
            return context.resources.pyspark.spark_session.read.parquet(path)
        elif context.dagster_type.typing_type == str:
            # return path to parquet files
            return path
        return check.failed(
            f"Inputs of type {context.dagster_type} not supported. Please specify a valid type "
            "for this input either in the solid signature or on the corresponding InputDefinition."
        )

    def _get_path(self, context: OutputContext):
        # filesystem-friendly string that is scoped to the start/end times of the data slice
        start, end = hourly_partitions.time_window_for_partition_key(context.partition_key)
        dt_format = "%Y%m%d%H%M%S"
        partition_str = start.strftime(dt_format) + "_" + end.strftime(dt_format)

        # if local fs path, store all outptus in same directory
        if "://" not in self._base_path:
            return os.path.join(self._base_path, f"{context.name}-{partition_str}.pq")
        # otherwise seperate into different dirs
        return os.path.join(self._base_path, context.name, f"{partition_str}.pq")

    def get_output_asset_key(self, context: OutputContext):
        return AssetKey([*self._base_path.split("://"), context.name])

    def get_output_asset_partitions(self, context: OutputContext):
        return [
            hourly_partitions.time_window_for_partition_key(context.partition_key).start.strftime(
                "%Y-%m-%d %H:%M:%S"
            )
        ]


@io_manager(
    config_schema={"base_path": Field(str, is_required=False)},
    required_resource_keys={"pyspark"},
)
def local_partitioned_parquet_io_manager(init_context):
    return PartitionedParquetIOManager(
        base_path=init_context.resource_config.get("base_path", get_system_temp_directory())
    )


@io_manager(required_resource_keys={"pyspark", "s3_bucket"})
def s3_partitioned_parquet_io_manager(init_context):
    return PartitionedParquetIOManager(base_path="s3://" + init_context.resources.s3_bucket)
