# start_repo_marker_0
import os

from dagster import (
    DagsterType,
    ModeDefinition,
    OutputDefinition,
    pipeline,
    repository,
    resource,
    solid,
)
from dagster.core.storage.asset_store import AssetStore
from pyspark.sql import Row, SparkSession
from pyspark.sql.types import IntegerType, StringType, StructField, StructType


class LocalParquetStore(AssetStore):
    def _get_path(self, context, step_output_handle):
        return os.path.join(
            context.run_id, step_output_handle.step_key, step_output_handle.output_name,
        )

    def set_asset(self, context, step_output_handle, obj, _):
        obj.write.parquet(self._get_path(context, step_output_handle))

    def get_asset(self, context, step_output_handle, _):
        spark = SparkSession.builder.getOrCreate()
        return spark.read.parquet()


@resource
def local_parquet_store(_):
    return LocalParquetStore()


@solid(output_defs=[OutputDefinition(asset_store_key="spark_asset_store")])
def make_people(_):
    schema = StructType([StructField("name", StringType()), StructField("age", IntegerType())])
    rows = [Row(name="Thom", age=51), Row(name="Jonny", age=48), Row(name="Nigel", age=49)]
    spark = SparkSession.builder.getOrCreate()
    return spark.createDataFrame(rows, schema)


@solid(output_defs=[OutputDefinition(asset_store_key="spark_asset_store")])
def filter_over_50(_, people):
    return people.filter(people["age"] > 50)


@solid(output_defs=[OutputDefinition(asset_store_key="spark_asset_store")])
def count_people(_, people) -> int:
    return people.count()


@pipeline(mode_defs=[ModeDefinition(resource_defs={"spark_asset_store": local_parquet_store})])
def my_pipeline():
    count_people(filter_over_50(make_people()))


# end_repo_marker_0


@repository
def basic_pyspark_repo():
    return [my_pipeline]
