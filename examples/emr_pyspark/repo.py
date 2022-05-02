# start-snippet
from pathlib import Path

from dagster_aws.emr import emr_pyspark_step_launcher
from dagster_aws.s3 import s3_resource
from dagster_pyspark import pyspark_resource
from pyspark.sql import DataFrame, Row
from pyspark.sql.types import IntegerType, StringType, StructField, StructType

from dagster import IOManager, ResourceDefinition, graph, io_manager, op, repository


class ParquetIOManager(IOManager):
    def _get_path(self, context):
        return "/".join(
            [context.resource_config["path_prefix"], context.run_id, context.step_key, context.name]
        )

    def handle_output(self, context, obj):
        obj.write.parquet(self._get_path(context))

    def load_input(self, context):
        spark = context.resources.pyspark.spark_session
        return spark.read.parquet(self._get_path(context.upstream_output))


@io_manager(required_resource_keys={"pyspark"}, config_schema={"path_prefix": str})
def parquet_io_manager():
    return ParquetIOManager()


@op(required_resource_keys={"pyspark", "pyspark_step_launcher"})
def make_people(context) -> DataFrame:
    schema = StructType([StructField("name", StringType()), StructField("age", IntegerType())])
    rows = [Row(name="Thom", age=51), Row(name="Jonny", age=48), Row(name="Nigel", age=49)]
    return context.resources.pyspark.spark_session.createDataFrame(rows, schema)


@op(required_resource_keys={"pyspark_step_launcher"})
def filter_over_50(people: DataFrame) -> DataFrame:
    return people.filter(people["age"] > 50)


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
    "io_manager": parquet_io_manager.configured({"path_prefix": "s3://my-s3-bucket"}),
}

local_resource_defs = {
    "pyspark_step_launcher": ResourceDefinition.none_resource(),
    "pyspark": pyspark_resource.configured({"spark_conf": {"spark.default.parallelism": 1}}),
    "io_manager": parquet_io_manager.configured({"path_prefix": "."}),
}


@graph
def make_and_filter_data():
    filter_over_50(make_people())


make_and_filter_data_local = make_and_filter_data.to_job(
    name="local", resource_defs=local_resource_defs
)

make_and_filter_data_emr = make_and_filter_data.to_job(name="prod", resource_defs=emr_resource_defs)

# end-snippet


@repository
def emr_pyspark_example():
    return [make_and_filter_data_emr, make_and_filter_data_local]
