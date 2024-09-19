import os
from typing import Union

import pandas
from dagster import (
    ConfigurableIOManager,
    InputContext,
    OutputContext,
    ResourceDependency,
    _check as check,
)
from dagster._seven.temp_dir import get_system_temp_directory
from dagster_pyspark.resources import PySparkResource
from pyspark.sql import DataFrame as PySparkDataFrame


class PartitionedParquetIOManager(ConfigurableIOManager):
    """This IOManager will take in a pandas or pyspark dataframe and store it in parquet at the
    specified path.

    It stores outputs for different partitions in different filepaths.

    Downstream ops can either load this dataframe into a spark session or simply retrieve a path
    to where the data is stored.
    """

    pyspark: ResourceDependency[PySparkResource]

    @property
    def _base_path(self):
        raise NotImplementedError()

    def handle_output(self, context: OutputContext, obj: Union[pandas.DataFrame, PySparkDataFrame]):
        path = self._get_path(context)
        if "://" not in self._base_path:
            os.makedirs(os.path.dirname(path), exist_ok=True)

        if isinstance(obj, pandas.DataFrame):
            row_count = len(obj)
            context.log.info(f"Row count: {row_count}")
            obj.to_parquet(path=path, index=False)
        elif isinstance(obj, PySparkDataFrame):
            row_count = obj.count()
            obj.write.parquet(path=path, mode="overwrite")
        else:
            raise Exception(f"Outputs of type {type(obj)} not supported.")

        context.add_output_metadata({"row_count": row_count, "path": path})

    def load_input(self, context) -> Union[PySparkDataFrame, str]:
        path = self._get_path(context)
        if context.dagster_type.typing_type == PySparkDataFrame:
            # return pyspark dataframe
            return self.pyspark.spark_session.read.parquet(path)

        return check.failed(
            f"Inputs of type {context.dagster_type} not supported. Please specify a valid type "
            "for this input either on the argument of the @asset-decorated function."
        )

    def _get_path(self, context: Union[InputContext, OutputContext]):
        key = context.asset_key.path[-1]

        if context.has_asset_partitions:
            start, end = context.asset_partitions_time_window
            dt_format = "%Y%m%d%H%M%S"
            partition_str = start.strftime(dt_format) + "_" + end.strftime(dt_format)
            return os.path.join(self._base_path, key, f"{partition_str}.pq")
        else:
            return os.path.join(self._base_path, f"{key}.pq")


class LocalPartitionedParquetIOManager(PartitionedParquetIOManager):
    base_path: str = get_system_temp_directory()

    @property
    def _base_path(self):
        return self.base_path


class S3PartitionedParquetIOManager(PartitionedParquetIOManager):
    s3_bucket: str

    @property
    def _base_path(self):
        return "s3://" + self.s3_bucket
