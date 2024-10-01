import os

from dagster import Definitions, load_assets_from_package_module
from dagster_aws.s3 import S3Resource
from dagster_aws.s3.io_manager import S3PickleIOManager
from dagster_dbt import DbtCliResource
from dagster_pyspark import pyspark_resource

from .assets import activity_analytics, core, dbt, recommender
from .constants import ACTIVITY_ANALYTICS, CORE, RECOMMENDER
from .jobs import activity_analytics_assets_sensor, core_assets_schedule, recommender_assets_sensor
from .project import DBT_PROJECT_DIR, dbt_project
from .resources.duckdb_parquet_io_manager import DuckDBPartitionedParquetIOManager
from .resources.hn_resource import HNAPIClient, HNAPISubsampleClient
from .resources.parquet_io_manager import (
    LocalPartitionedParquetIOManager,
    S3PartitionedParquetIOManager,
)
from .resources.snowflake_io_manager import SnowflakeIOManager
from .sensors.slack_on_failure_sensor import make_slack_on_failure_sensor

core_assets = load_assets_from_package_module(core, group_name=CORE)

activity_analytics_assets = load_assets_from_package_module(
    activity_analytics,
    key_prefix=["snowflake", ACTIVITY_ANALYTICS],
    group_name=ACTIVITY_ANALYTICS,
)

recommender_assets = load_assets_from_package_module(recommender, group_name=RECOMMENDER)

dbt_assets = load_assets_from_package_module(dbt)

all_assets = [
    *core_assets,
    *recommender_assets,
    *activity_analytics_assets,
    *dbt_assets,
]

dbt_local_resource = DbtCliResource(
    project_dir=dbt_project,
    target="local",
)
dbt_staging_resource = DbtCliResource(
    project_dir=dbt_project,
    target="staging",
)
dbt_prod_resource = DbtCliResource(
    project_dir=dbt_project,
    target="prod",
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

RESOURCES_PROD = {
    "io_manager": S3PickleIOManager(
        s3_resource=S3Resource.configure_at_launch(),
        s3_bucket="hackernews-elementl-prod",
    ),
    "parquet_io_manager": S3PartitionedParquetIOManager(
        pyspark=configured_pyspark, s3_bucket="hackernews-elementl-dev"
    ),
    "warehouse_io_manager": SnowflakeIOManager(database="DEMO_DB", **SHARED_SNOWFLAKE_CONF),
    "hn_client": HNAPISubsampleClient(subsample_rate=10),
    "dbt": dbt_prod_resource,
}


RESOURCES_STAGING = {
    "io_manager": S3PickleIOManager(
        s3_resource=S3Resource.configure_at_launch(),
        s3_bucket="hackernews-elementl-dev",
    ),
    "parquet_io_manager": S3PartitionedParquetIOManager(
        pyspark=configured_pyspark, s3_bucket="hackernews-elementl-dev"
    ),
    "warehouse_io_manager": SnowflakeIOManager(database="DEMO_DB_STAGING", **SHARED_SNOWFLAKE_CONF),
    "hn_client": HNAPISubsampleClient(subsample_rate=10),
    "dbt": dbt_staging_resource,
}


RESOURCES_LOCAL = {
    "parquet_io_manager": LocalPartitionedParquetIOManager(pyspark=configured_pyspark),
    "warehouse_io_manager": DuckDBPartitionedParquetIOManager(
        pyspark=configured_pyspark,
        duckdb_path=os.path.join(DBT_PROJECT_DIR, "hackernews.duckdb"),
    ),
    "hn_client": HNAPIClient(),
    "dbt": dbt_local_resource,
}


resources_by_deployment_name = {
    "prod": RESOURCES_PROD,
    "staging": RESOURCES_STAGING,
    "local": RESOURCES_LOCAL,
}

deployment_name = os.environ.get("DAGSTER_DEPLOYMENT", "local")

all_sensors = [activity_analytics_assets_sensor, recommender_assets_sensor]
if deployment_name in ["prod", "staging"]:
    all_sensors.append(make_slack_on_failure_sensor(base_url="my_webserver_url"))

defs = Definitions(
    assets=all_assets,
    resources=resources_by_deployment_name[deployment_name],
    schedules=[core_assets_schedule],
    sensors=all_sensors,
)
