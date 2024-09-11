from pathlib import Path
from typing import Any

from dagster_aws.emr import emr_pyspark_step_launcher
from dagster_aws.s3 import S3Resource
from dagster_pyspark import PySparkResource
from pyspark.sql import DataFrame, Row
from pyspark.sql.types import IntegerType, StringType, StructField, StructType

import dagster as dg

emr_pyspark = PySparkResource(spark_config={"spark.executor.memory": "2g"})


@dg.asset
def people(
    pyspark: PySparkResource, pyspark_step_launcher: dg.ResourceParam[Any]
) -> DataFrame:
    schema = StructType(
        [StructField("name", StringType()), StructField("age", IntegerType())]
    )
    rows = [
        Row(name="Thom", age=51),
        Row(name="Jonny", age=48),
        Row(name="Nigel", age=49),
    ]
    return pyspark.spark_session.createDataFrame(rows, schema)


@dg.asset
def people_over_50(
    pyspark_step_launcher: dg.ResourceParam[Any], people: DataFrame
) -> DataFrame:
    return people.filter(people["age"] > 50)


defs = dg.Definitions(
    assets=[people, people_over_50],
    resources={
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
    },
)
