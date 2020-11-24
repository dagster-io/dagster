# start_repo_marker_0
import os

from dagster import ModeDefinition, pipeline, repository, resource, solid
from dagster.core.storage.asset_store import AssetStore
from pyspark.sql import Row, SparkSession
from pyspark.sql.types import IntegerType, StringType, StructField, StructType


class LocalParquetStore(AssetStore):
    def _get_path(self, context):
        return os.path.join(context.source_run_id, context.step_key, context.output_name)

    def set_asset(self, context, obj):
        obj.write.parquet(self._get_path(context))

    def get_asset(self, context):
        spark = SparkSession.builder.getOrCreate()
        return spark.read.parquet(self._get_path(context))


@resource
def local_parquet_store(_):
    return LocalParquetStore()


@solid
def make_people(_):
    schema = StructType([StructField("name", StringType()), StructField("age", IntegerType())])
    rows = [Row(name="Thom", age=51), Row(name="Jonny", age=48), Row(name="Nigel", age=49)]
    spark = SparkSession.builder.getOrCreate()
    return spark.createDataFrame(rows, schema)


@solid
def filter_over_50(_, people):
    return people.filter(people["age"] > 50)


@pipeline(mode_defs=[ModeDefinition(resource_defs={"asset_store": local_parquet_store})])
def my_pipeline():
    filter_over_50(make_people())


# end_repo_marker_0


@repository
def basic_pyspark_repo():
    return [my_pipeline]
