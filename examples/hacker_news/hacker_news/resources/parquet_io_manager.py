import os
from typing import Union

import pandas
import pyspark
from dagster import AssetKey, EventMetadataEntry, IOManager, OutputContext, check, io_manager


class ParquetIOManager(IOManager):
    """
    This IOManager will take in a pandas or pyspark dataframe and store it in parquet at the
    specified path.

    Downstream solids can either load this dataframe into a spark session or simply retrieve a path
    to where the data is stored.
    """

    def _get_path(self, context: OutputContext):

        base_path = context.resource_config["base_path"]

        return os.path.join(base_path, f"{context.name}.pq")

    def get_output_asset_key(self, context: OutputContext):
        return AssetKey([*context.resource_config["base_path"].split("://"), context.name])

    def handle_output(
        self, context: OutputContext, obj: Union[pandas.DataFrame, pyspark.sql.DataFrame]
    ):

        path = self._get_path(context)
        if isinstance(obj, pandas.DataFrame):
            row_count = len(obj)
            obj.to_parquet(path=path)
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


class PartitionedParquetIOManager(ParquetIOManager):
    """
    This works similarly to the normal ParquetIOManager, but stores outputs for different partitions
    in different filepaths.
    """

    def _get_path(self, context: OutputContext):

        base_path = context.resource_config["base_path"]

        # filesystem-friendly string that is scoped to the start/end times of the data slice
        partition_str = f"{context.resources.partition_start}_{context.resources.partition_end}"
        partition_str = "".join(c for c in partition_str if c == "_" or c.isdigit())

        # if local fs path, store all outptus in same directory
        if "://" not in base_path:
            return os.path.join(base_path, f"{context.name}-{partition_str}.pq")
        # otherwise seperate into different dirs
        return os.path.join(base_path, context.name, f"{partition_str}.pq")

    def get_output_asset_partitions(self, context: OutputContext):
        return set([context.resources.partition_start])


@io_manager(
    config_schema={"base_path": str},
    required_resource_keys={"pyspark"},
)
def parquet_io_manager(_):
    return ParquetIOManager()


@io_manager(
    config_schema={"base_path": str},
    required_resource_keys={"pyspark", "partition_start", "partition_end"},
)
def partitioned_parquet_io_manager(_):
    return PartitionedParquetIOManager()
