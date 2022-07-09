# start_repo_marker_0
import os

from pyspark.sql import DataFrame, Row, SparkSession
from pyspark.sql.types import IntegerType, StringType, StructField, StructType

from dagster import IOManager, graph, io_manager, op, repository


class LocalParquetIOManager(IOManager):
    def _get_path(self, context):
        return os.path.join(context.run_id, context.step_key, context.name)

    def handle_output(self, context, obj):
        obj.write.parquet(self._get_path(context))

    def load_input(self, context):
        spark = SparkSession.builder.getOrCreate()
        return spark.read.parquet(self._get_path(context.upstream_output))


@io_manager
def local_parquet_io_manager():
    return LocalParquetIOManager()


@op
def make_people() -> DataFrame:
    schema = StructType([StructField("name", StringType()), StructField("age", IntegerType())])
    rows = [Row(name="Thom", age=51), Row(name="Jonny", age=48), Row(name="Nigel", age=49)]
    spark = SparkSession.builder.getOrCreate()
    return spark.createDataFrame(rows, schema)


@op
def filter_over_50(people: DataFrame) -> DataFrame:
    return people.filter(people["age"] > 50)


@graph
def make_and_filter_data():
    filter_over_50(make_people())


make_and_filter_data_job = make_and_filter_data.to_job(
    resource_defs={"io_manager": local_parquet_io_manager}
)


# end_repo_marker_0


@repository
def basic_pyspark_repo():
    return [make_and_filter_data_job]
