import os
from typing import Optional

from dagster._seven.temp_dir import get_system_temp_directory
from dagster_aws.s3 import s3_resource
from dagster_aws.s3.io_manager import PickledObjectS3IOManager
from dagster_aws.s3.utils import construct_s3_client
from dagster_dbt import dbt_cli_resource
from dagster_pyspark.resources import PySparkResource

from dagster._utils import file_relative_path

from .common_bucket_s3_pickle_io_manager import common_bucket_s3_pickle_io_manager
from .duckdb_parquet_io_manager import duckdb_partitioned_parquet_io_manager
from .hn_resource import hn_api_client, hn_api_subsample_client, HNAPISubsampleClient
from .parquet_io_manager import PartitionedParquetIOManager
from .snowflake_io_manager import snowflake_io_manager

DBT_PROJECT_DIR = file_relative_path(__file__, "../../dbt_project")
DBT_PROFILES_DIR = DBT_PROJECT_DIR + "/config"
dbt_local_resource = dbt_cli_resource.configured(
    {"profiles_dir": DBT_PROFILES_DIR, "project_dir": DBT_PROJECT_DIR, "target": "local"}
)
dbt_staging_resource = dbt_cli_resource.configured(
    {"profiles-dir": DBT_PROFILES_DIR, "project-dir": DBT_PROJECT_DIR, "target": "staging"}
)
dbt_prod_resource = dbt_cli_resource.configured(
    {"profiles_dir": DBT_PROFILES_DIR, "project_dir": DBT_PROJECT_DIR, "target": "prod"}
)


def create_local_partitioned_io_manager(
    pyspark_resource: PySparkResource, base_path: Optional[str] = None
) -> PartitionedParquetIOManager:
    return PartitionedParquetIOManager(
        base_path=base_path if base_path is not None else get_system_temp_directory(),
        pyspark_resource=pyspark_resource,
    )


def create_s3_partitioned_parquet_io_manager(
    pyspark_resource: PySparkResource, s3_bucket
) -> PartitionedParquetIOManager:
    return PartitionedParquetIOManager(
        base_path="s3://" + s3_bucket, pyspark_resource=pyspark_resource
    )


def get_spark_conf():
    return {
        "spark.jars.packages": ",".join(
            [
                "net.snowflake:snowflake-jdbc:3.8.0",
                "net.snowflake:spark-snowflake_2.12:2.8.2-spark_3.0",
                "com.amazonaws:aws-java-sdk:1.7.4,org.apache.hadoop:hadoop-aws:2.7.7",
            ]
        ),
        "spark.hadoop.fs.s3.impl": "org.apache.hadoop.fs.s3native.NativeS3FileSystem",
        "spark.hadoop.fs.s3.awsAccessKeyId": os.getenv("AWS_ACCESS_KEY_ID", ""),
        "spark.hadoop.fs.s3.awsSecretAccessKey": os.getenv("AWS_SECRET_ACCESS_KEY", ""),
        "spark.hadoop.fs.s3.buffer.dir": "/tmp",
    }


configured_pyspark = PySparkResource({"spark_conf": get_spark_conf()})


snowflake_io_manager_prod = snowflake_io_manager.configured({"database": "DEMO_DB"})


def get_prod_resources():
    s3_bucket = "hackernews-elementl-prod"
    s3_session = construct_s3_client(max_attempts=5)
    return {
        "io_manager": PickledObjectS3IOManager(s3_bucket=s3_bucket, s3_session=s3_session),
        "s3": s3_resource,
        "parquet_io_manager": create_s3_partitioned_parquet_io_manager(
            pyspark_resource=configured_pyspark, s3_bucket=s3_bucket
        ),
        "warehouse_io_manager": snowflake_io_manager_prod,
        "pyspark": configured_pyspark,
        "hn_client": HNAPISubsampleClient(subsample_rate=10),
        "dbt": dbt_prod_resource,
    }


RESOURCES_PROD = get_prod_resources()

snowflake_io_manager_staging = snowflake_io_manager.configured({"database": "DEMO_DB_STAGING"})


def get_staging_resources():
    s3_bucket = "hackernews-elementl-dev"
    return {
        "io_manager": PickledObjectS3IOManager(
            s3_bucket=s3_bucket, s3_session=construct_s3_client(max_attempts=5)
        ),
        "s3": s3_resource,
        "parquet_io_manager": create_s3_partitioned_parquet_io_manager(
            pyspark_resource=configured_pyspark, s3_bucket=s3_bucket
        ),
        "warehouse_io_manager": snowflake_io_manager_staging,
        "pyspark": configured_pyspark,
        "hn_client": HNAPISubsampleClient(subsample_rate=10),
        "dbt": dbt_staging_resource,
    }


RESOURCES_LOCAL = {
    "parquet_io_manager": create_local_partitioned_io_manager(configured_pyspark),
    "warehouse_io_manager": duckdb_partitioned_parquet_io_manager.configured(
        {"duckdb_path": os.path.join(DBT_PROJECT_DIR, "hackernews.duckdb")},
    ),
    "pyspark": configured_pyspark,
    "hn_client": hn_api_client,
    "dbt": dbt_local_resource,
}
