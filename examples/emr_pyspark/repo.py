from dagster_aws.emr import emr_pyspark_step_launcher
from dagster_aws.s3 import s3_plus_default_intermediate_storage_defs, s3_resource
from dagster_pyspark import DataFrame as DagsterPySparkDataFrame
from dagster_pyspark import pyspark_resource
from pyspark.sql import DataFrame, Row
from pyspark.sql.types import IntegerType, StringType, StructField, StructType

from dagster import (
    ModeDefinition,
    PresetDefinition,
    make_python_type_usable_as_dagster_type,
    pipeline,
    repository,
    solid,
)
from dagster.core.definitions.no_step_launcher import no_step_launcher

# Make pyspark.sql.DataFrame map to dagster_pyspark.DataFrame
make_python_type_usable_as_dagster_type(python_type=DataFrame, dagster_type=DagsterPySparkDataFrame)


@solid(required_resource_keys={"pyspark", "pyspark_step_launcher"})
def make_people(context) -> DataFrame:
    schema = StructType([StructField("name", StringType()), StructField("age", IntegerType())])
    rows = [Row(name="Thom", age=51), Row(name="Jonny", age=48), Row(name="Nigel", age=49)]
    return context.resources.pyspark.spark_session.createDataFrame(rows, schema)


@solid(required_resource_keys={"pyspark_step_launcher"})
def filter_over_50(_, people: DataFrame) -> DataFrame:
    return people.filter(people["age"] > 50)


@solid(required_resource_keys={"pyspark_step_launcher"})
def count_people(_, people: DataFrame) -> int:
    return people.count()


emr_mode = ModeDefinition(
    name="emr",
    resource_defs={
        "pyspark_step_launcher": emr_pyspark_step_launcher,
        "pyspark": pyspark_resource,
        "s3": s3_resource,
    },
    intermediate_storage_defs=s3_plus_default_intermediate_storage_defs,
)

emr_preset = PresetDefinition.from_pkg_resources(
    name="emr",
    mode="emr",
    pkg_resource_defs=[("emr_pyspark", "prod_resources.yaml"), ("emr_pyspark", "s3_storage.yaml")],
)


local_mode = ModeDefinition(
    name="local",
    resource_defs={"pyspark_step_launcher": no_step_launcher, "pyspark": pyspark_resource},
)


@pipeline(
    mode_defs=[emr_mode, local_mode], preset_defs=[emr_preset],
)
def my_pipeline():
    count_people(filter_over_50(make_people()))


@repository
def emr_pyspark_example():
    return [my_pipeline]
