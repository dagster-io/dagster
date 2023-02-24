import os

from dagster._utils import file_relative_path
from dagster_aws.s3 import s3_resource
from dagster_dbt import dbt_cli_resource
from dagster_duckdb import build_duckdb_io_manager
from dagster_duckdb_pandas import DuckDBPandasTypeHandler
from dagster_duckdb_pyspark import DuckDBPySparkTypeHandler
from dagster_pyspark import pyspark_resource
from dagster_snowflake import build_snowflake_io_manager
from dagster_snowflake_pandas import SnowflakePandasTypeHandler
from dagster_snowflake_pyspark import SnowflakePySparkTypeHandler

from .common_bucket_s3_pickle_io_manager import common_bucket_s3_pickle_io_manager
from .hn_resource import HNAPIClient, HNAPISubsampleClient
from .parquet_io_manager import (
    local_partitioned_parquet_io_manager,
    s3_partitioned_parquet_io_manager,
)

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


configured_pyspark = pyspark_resource.configured(
    {
        "spark_conf": {
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
    }
)

SHARED_SNOWFLAKE_CONF = {
    "account": os.getenv("SNOWFLAKE_ACCOUNT", ""),
    "user": os.getenv("SNOWFLAKE_USER", ""),
    "password": os.getenv("SNOWFLAKE_PASSWORD", ""),
    "warehouse": "TINY_WAREHOUSE",
}

snowflake_io_manager = build_snowflake_io_manager(
    [SnowflakePandasTypeHandler(), SnowflakePySparkTypeHandler()]
)

RESOURCES_PROD = {
    "s3_bucket": "hackernews-elementl-prod",
    "io_manager": common_bucket_s3_pickle_io_manager,
    "s3": s3_resource,
    "parquet_io_manager": s3_partitioned_parquet_io_manager,
    "warehouse_io_manager": snowflake_io_manager.configured(
        dict(database="DEMO_DB", **SHARED_SNOWFLAKE_CONF)
    ),
    "pyspark": configured_pyspark,
    "hn_client": HNAPISubsampleClient(subsample_rate=10),
    "dbt": dbt_prod_resource,
}


RESOURCES_STAGING = {
    "s3_bucket": "hackernews-elementl-dev",
    "io_manager": common_bucket_s3_pickle_io_manager,
    "s3": s3_resource,
    "parquet_io_manager": s3_partitioned_parquet_io_manager,
    "warehouse_io_manager": snowflake_io_manager.configured(
        dict(database="DEMO_DB_STAGING", **SHARED_SNOWFLAKE_CONF)
    ),
    "pyspark": configured_pyspark,
    "hn_client": HNAPISubsampleClient(subsample_rate=10),
    "dbt": dbt_staging_resource,
}

duckdb_io_manager = build_duckdb_io_manager([DuckDBPandasTypeHandler(), DuckDBPySparkTypeHandler()])

RESOURCES_LOCAL = {
    "parquet_io_manager": local_partitioned_parquet_io_manager,
    "warehouse_io_manager": duckdb_io_manager.configured(
        {"database": os.path.join(DBT_PROJECT_DIR, "hackernews.duckdb")},
    ),
    "pyspark": configured_pyspark,
    "hn_client": HNAPIClient(),
    "dbt": dbt_local_resource,
}
