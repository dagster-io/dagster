import os

from dagster import ConfigurableIOManager, Definitions, asset
from pyspark.sql import DataFrame, Row, SparkSession
from pyspark.sql.types import IntegerType, StringType, StructField, StructType


class LocalParquetIOManager(ConfigurableIOManager):
    def _get_path(self, context):
        return os.path.join(*context.asset_key.path)

    def handle_output(self, context, obj):
        obj.write.parquet(self._get_path(context))

    def load_input(self, context):
        spark = SparkSession.builder.getOrCreate()
        return spark.read.parquet(self._get_path(context.upstream_output))


@asset
def people() -> DataFrame:
    schema = StructType([StructField("name", StringType()), StructField("age", IntegerType())])
    rows = [Row(name="Thom", age=51), Row(name="Jonny", age=48), Row(name="Nigel", age=49)]
    spark = SparkSession.builder.getOrCreate()  # type: ignore
    return spark.createDataFrame(rows, schema)


@asset
def people_over_50(people: DataFrame) -> DataFrame:
    return people.filter(people["age"] > 50)


defs = Definitions(
    assets=[people, people_over_50], resources={"io_manager": LocalParquetIOManager()}
)
