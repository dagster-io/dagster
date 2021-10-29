import os
from typing import Union

import pandas
from dagster import EventMetadataEntry, IOManager, OutputContext, io_manager


class ParquetIOManager(IOManager):
    """
    This IOManager will take in a pandas or pyspark dataframe and store it in parquet at the
    specified path.

    Downstream solids can either load this dataframe into a spark session or simply retrieve a path
    to where the data is stored.
    """

    def _get_path(self, context: OutputContext):

        base_path = context.resource_config["base_path"]

        return os.path.join(base_path, f"{context.asset_key.path[-1]}.pq")

    def handle_output(self, context: OutputContext, obj: pandas.DataFrame):

        path = self._get_path(context)
        if isinstance(obj, pandas.DataFrame):
            row_count = len(obj)
            obj.to_parquet(path=path, index=False)
        else:
            raise Exception(f"Outputs of type {type(obj)} not supported.")
        yield EventMetadataEntry.int(value=row_count, label="row_count")
        yield EventMetadataEntry.path(path=path, label="path")
        yield EventMetadataEntry.text(text=", ".join(obj.columns), label="columns")

    def load_input(self, context) -> Union[pandas.DataFrame, str]:
        path = self._get_path(context.upstream_output)
        return pandas.read_parquet(path)


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
            return os.path.join(base_path, f"{context.asset_key.path[-1]}-{partition_str}.pq")
        # otherwise seperate into different dirs
        return os.path.join(base_path, context.asset_key.path[-1], f"{partition_str}.pq")

    def get_output_asset_partitions(self, context: OutputContext):
        return set([context.resources.partition_start])


@io_manager(
    config_schema={"base_path": str},
)
def parquet_io_manager(_):
    return ParquetIOManager()


@io_manager(
    config_schema={"base_path": str},
    required_resource_keys={"partition_start", "partition_end"},
)
def partitioned_parquet_io_manager(_):
    return PartitionedParquetIOManager()
