# start-snippet
from pathlib import Path

from dagster_aws.s3 import s3_intermediate_storage, s3_resource
from dagster_aws_pyspark import emr_pyspark_step_launcher
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
        "pyspark_step_launcher": emr_pyspark_step_launcher.configured(
            {
                "cluster_id": {"env": "EMR_CLUSTER_ID"},
                "local_pipeline_package_path": str(Path(__file__).parent),
                "deploy_local_pipeline_package": True,
                "region_name": "us-west-1",
                "staging_bucket": "my_staging_bucket",
                "wait_for_logs": True,
            }
        ),
        "pyspark": pyspark_resource.configured({"spark_conf": {"spark.executor.memory": "2g"}}),
        "s3": s3_resource,
    },
    intermediate_storage_defs=[
        s3_intermediate_storage.configured(
            {"s3_bucket": "my_staging_bucket", "s3_prefix": "simple-pyspark"}
        )
    ],
)

local_mode = ModeDefinition(
    name="local",
    resource_defs={
        "pyspark_step_launcher": no_step_launcher,
        "pyspark": pyspark_resource.configured({"spark_conf": {"spark.default.parallelism": 1}}),
    },
)


@pipeline(mode_defs=[emr_mode, local_mode])
def my_pipeline():
    count_people(filter_over_50(make_people()))


# end-snippet


@repository
def emr_pyspark_example():
    return [my_pipeline]
