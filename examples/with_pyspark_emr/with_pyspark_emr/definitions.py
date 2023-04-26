from pathlib import Path
from typing import Any

from dagster import (
    ConfigurableIOManager,
    Definitions,
    ResourceDefinition,
    ResourceParam,
    graph,
    op,
)
from dagster_aws.emr import emr_pyspark_step_launcher
from dagster_aws.s3 import S3Resource
from dagster_pyspark import PySparkResource
from pyspark.sql import DataFrame, Row
from pyspark.sql.types import IntegerType, StringType, StructField, StructType


class ParquetIOManager(ConfigurableIOManager):
    pyspark: PySparkResource
    path_prefix: str

    def _get_path(self, context) -> str:
        return "/".join([self.path_prefix, context.run_id, context.step_key, context.name])

    def handle_output(self, context, obj):
        obj.write.parquet(self._get_path(context))

    def load_input(self, context):
        spark = self.pyspark.get_client().spark_session
        return spark.read.parquet(self._get_path(context.upstream_output))


@op
def make_people(pyspark: PySparkResource, pyspark_step_launcher: ResourceParam[Any]) -> DataFrame:
    schema = StructType([StructField("name", StringType()), StructField("age", IntegerType())])
    rows = [Row(name="Thom", age=51), Row(name="Jonny", age=48), Row(name="Nigel", age=49)]
    return pyspark.get_client().spark_session.createDataFrame(rows, schema)


@op
def filter_over_50(pyspark_step_launcher: ResourceParam[Any], people: DataFrame) -> DataFrame:
    return people.filter(people["age"] > 50)


emr_pyspark = PySparkResource(spark_config={"spark.executor.memory": "2g"})
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
    "pyspark": emr_pyspark,
    "s3": S3Resource(),
    "io_manager": ParquetIOManager(pyspark=emr_pyspark, path_prefix="s3://my-s3-bucket"),
}

local_pyspark = PySparkResource(spark_config={"spark.default.parallelism": 1})
local_resource_defs = {
    "pyspark_step_launcher": ResourceDefinition.none_resource(),
    "pyspark": local_pyspark,
    "io_manager": ParquetIOManager(pyspark=local_pyspark, path_prefix="."),
}


@graph
def make_and_filter_data():
    filter_over_50(make_people())


make_and_filter_data_local = make_and_filter_data.to_job(
    name="local", resource_defs=local_resource_defs
)

make_and_filter_data_emr = make_and_filter_data.to_job(name="prod", resource_defs=emr_resource_defs)

defs = Definitions(jobs=[make_and_filter_data_emr, make_and_filter_data_local])
