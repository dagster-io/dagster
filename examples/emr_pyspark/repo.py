# start-snippet
from pathlib import Path

from dagster import graph, make_python_type_usable_as_dagster_type, op, repository
from dagster.core.definitions.no_step_launcher import no_step_launcher
from dagster_aws.emr import emr_pyspark_step_launcher
from dagster_aws.s3 import s3_pickle_io_manager, s3_resource
from dagster_pyspark import DataFrame as DagsterPySparkDataFrame
from dagster_pyspark import pyspark_resource
from pyspark.sql import DataFrame, Row
from pyspark.sql.types import IntegerType, StringType, StructField, StructType

# Make pyspark.sql.DataFrame map to dagster_pyspark.DataFrame
make_python_type_usable_as_dagster_type(python_type=DataFrame, dagster_type=DagsterPySparkDataFrame)


@op(required_resource_keys={"pyspark", "pyspark_step_launcher"})
def make_people(context) -> DataFrame:
    schema = StructType([StructField("name", StringType()), StructField("age", IntegerType())])
    rows = [Row(name="Thom", age=51), Row(name="Jonny", age=48), Row(name="Nigel", age=49)]
    return context.resources.pyspark.spark_session.createDataFrame(rows, schema)


@op(required_resource_keys={"pyspark_step_launcher"})
def filter_over_50(people: DataFrame) -> DataFrame:
    return people.filter(people["age"] > 50)


@op(required_resource_keys={"pyspark_step_launcher"})
def count_people(people: DataFrame) -> int:
    return people.count()


emr_resource_defs = {
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
    "io_manager": s3_pickle_io_manager.configured(
        {"s3_bucket": "my_staging_bucket", "s3_prefix": "simple-pyspark"}
    ),
}

local_resource_defs = {
    "pyspark_step_launcher": no_step_launcher,
    "pyspark": pyspark_resource.configured({"spark_conf": {"spark.default.parallelism": 1}}),
}


@graph
def count_people_over_50():
    count_people(filter_over_50(make_people()))


count_people_over_50_local = count_people_over_50.to_job(
    name="local", resource_defs=local_resource_defs
)

count_people_over_50_emr = count_people_over_50.to_job(name="prod", resource_defs=emr_resource_defs)

# end-snippet


@repository
def emr_pyspark_example():
    return [count_people_over_50_emr, count_people_over_50_local]
