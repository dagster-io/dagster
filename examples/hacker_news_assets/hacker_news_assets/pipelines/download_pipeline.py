import os

from dagster import ResourceDefinition, fs_io_manager
from dagster.core.asset_defs import build_assets_job
from dagster.seven.temp_dir import get_system_temp_directory
from dagster_aws.s3 import s3_pickle_io_manager, s3_resource
from dagster_pyspark import pyspark_resource
from hacker_news_assets.resources.hn_resource import hn_api_subsample_client
from hacker_news_assets.resources.parquet_io_manager import partitioned_parquet_io_manager
from hacker_news_assets.resources.snowflake_io_manager import time_partitioned_snowflake_io_manager
from hacker_news_assets.solids.download_items import comments_and_stories_lake, items
from hacker_news_assets.solids.id_range_for_time import id_range_for_time
from hacker_news_assets.solids.upload_to_database import comments, stories

# the configuration we'll need to make our Snowflake-based IOManager work
SNOWFLAKE_CONF = {
    "account": os.getenv("SNOWFLAKE_ACCOUNT", ""),
    "user": os.getenv("SNOWFLAKE_USER", ""),
    "password": os.getenv("SNOWFLAKE_PASSWORD", ""),
    "database": "DEMO_DB",
    "warehouse": "TINY_WAREHOUSE",
}

# the configuration we'll need to make spark able to read from / write to s3
S3_SPARK_CONF = {
    "spark_conf": {
        "spark.jars.packages": "com.amazonaws:aws-java-sdk:1.7.4,org.apache.hadoop:hadoop-aws:2.7.7",
        "spark.hadoop.fs.s3.impl": "org.apache.hadoop.fs.s3native.NativeS3FileSystem",
        "spark.hadoop.fs.s3.awsAccessKeyId": os.getenv("AWS_ACCESS_KEY_ID", ""),
        "spark.hadoop.fs.s3.awsSecretAccessKey": os.getenv("AWS_SECRET_ACCESS_KEY", ""),
        "spark.hadoop.fs.s3.buffer.dir": "/tmp",
    }
}


DEV_RESOURCES = {
    "io_manager": fs_io_manager,
    "partition_start": ResourceDefinition.string_resource(),
    "partition_end": ResourceDefinition.string_resource(),
    "parquet_io_manager": partitioned_parquet_io_manager.configured(
        {"base_path": get_system_temp_directory()}
    ),
    "db_io_manager": fs_io_manager,
    "pyspark": pyspark_resource,
    "hn_client": hn_api_subsample_client.configured({"sample_rate": 10}),
}


PROD_RESOURCES = {
    "io_manager": s3_pickle_io_manager.configured({"s3_bucket": "hackernews-elementl-prod"}),
    "s3": s3_resource,
    "partition_start": ResourceDefinition.string_resource(),
    "partition_end": ResourceDefinition.string_resource(),
    "parquet_io_manager": partitioned_parquet_io_manager.configured(
        {"base_path": "s3://hackernews-elementl-prod"}
    ),
    "db_io_manager": time_partitioned_snowflake_io_manager.configured(SNOWFLAKE_CONF),
    "pyspark": pyspark_resource.configured(S3_SPARK_CONF),
    "hn_client": hn_api_subsample_client.configured({"sample_rate": 10}),
}

download_pipeline_properties = {
    "description": "#### Owners:\n"
    "schrockn@elementl.com, cat@elementl.com\n "
    "#### About\n"
    "This pipeline downloads all items from the HN API for a given day, "
    "splits the items into stories and comment types using Spark, and uploads filtered items to "
    "the corresponding stories or comments Snowflake table",
    "tags": {
        "dagster-k8s/config": {
            "container_config": {
                "resources": {
                    "requests": {"cpu": "500m", "memory": "2Gi"},
                }
            },
        }
    },
}

assets = [id_range_for_time, items, comments_and_stories_lake, comments, stories]

download_comments_and_stories_dev = build_assets_job(
    "download_comments_and_stories_dev",
    assets=assets,
    resource_defs=DEV_RESOURCES,
    description=(
        "This job queries live HN data but does all writes locally. "
        "It is meant to be used on a local machine"
    ),
)

download_comments_and_stories_prod = build_assets_job(
    "download_comments_and_stories_prod",
    assets=assets,
    resource_defs=PROD_RESOURCES,
    description=(
        "This mode queries live HN data and writes to a prod S3 bucket."
        "Intended for use in production."
    ),
)
