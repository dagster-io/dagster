# start_repo_marker_0
from dagster_pyspark import DataFrame as DagsterPySparkDataFrame
from dagster_pyspark import pyspark_resource
from pyspark.sql import DataFrame, Row
from pyspark.sql.types import IntegerType, StringType, StructField, StructType

from dagster import (
    ModeDefinition,
    make_python_type_usable_as_dagster_type,
    pipeline,
    repository,
    solid,
)

# Make pyspark.sql.DataFrame map to dagster_pyspark.DataFrame
make_python_type_usable_as_dagster_type(python_type=DataFrame, dagster_type=DagsterPySparkDataFrame)


@solid(required_resource_keys={"pyspark"})
def make_people(context) -> DataFrame:
    schema = StructType([StructField("name", StringType()), StructField("age", IntegerType())])
    rows = [Row(name="Thom", age=51), Row(name="Jonny", age=48), Row(name="Nigel", age=49)]
    return context.resources.pyspark.spark_session.createDataFrame(rows, schema)


@solid
def filter_over_50(_, people: DataFrame) -> DataFrame:
    return people.filter(people["age"] > 50)


@solid
def count_people(_, people: DataFrame) -> int:
    return people.count()


@pipeline(mode_defs=[ModeDefinition(resource_defs={"pyspark": pyspark_resource})])
def my_pipeline():
    count_people(filter_over_50(make_people()))


# end_repo_marker_0


@repository
def basic_pyspark_repo():
    return [my_pipeline]
