import os
from datetime import datetime

from dagster import ResourceDefinition, graph, hourly_partitioned_config
from dagster_aws.s3 import s3_pickle_io_manager, s3_resource
from dagster_pyspark import pyspark_resource
from hacker_news.ops.download_items import build_comments, build_stories, download_items
from hacker_news.ops.id_range_for_time import id_range_for_time
from hacker_news.resources.hn_resource import hn_api_subsample_client
from hacker_news.resources.parquet_io_manager import partitioned_parquet_io_manager
from hacker_news.resources.snowflake_io_manager import time_partitioned_snowflake_io_manager

# the configuration we'll need to make our Snowflake-based IOManager work
SNOWFLAKE_CONF = {
    "account": os.getenv("SNOWFLAKE_ACCOUNT", ""),
    "user": os.getenv("SNOWFLAKE_USER", ""),
    "password": os.getenv("SNOWFLAKE_PASSWORD", ""),
    "database": "DEMO_DB",
    "warehouse": "TINY_WAREHOUSE",
}

# the configuration we'll need to make spark able to read from / write to s3
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

DOWNLOAD_RESOURCES_STAGING = {
    "io_manager": s3_pickle_io_manager.configured({"s3_bucket": "hackernews-elementl-dev"}),
    "s3": s3_resource,
    "partition_start": ResourceDefinition.string_resource(),
    "partition_end": ResourceDefinition.string_resource(),
    "parquet_io_manager": partitioned_parquet_io_manager.configured(
        {"base_path": "s3://hackernews-elementl-dev"}
    ),
    "warehouse_io_manager": time_partitioned_snowflake_io_manager.configured(SNOWFLAKE_CONF),
    "pyspark": configured_pyspark,
    "hn_client": hn_api_subsample_client.configured({"sample_rate": 10}),
}

DOWNLOAD_RESOURCES_PROD = {
    "io_manager": s3_pickle_io_manager.configured({"s3_bucket": "hackernews-elementl-prod"}),
    "s3": s3_resource,
    "partition_start": ResourceDefinition.string_resource(),
    "partition_end": ResourceDefinition.string_resource(),
    "parquet_io_manager": partitioned_parquet_io_manager.configured(
        {"base_path": "s3://hackernews-elementl-prod"}
    ),
    "warehouse_io_manager": time_partitioned_snowflake_io_manager.configured(SNOWFLAKE_CONF),
    "pyspark": configured_pyspark,
    "hn_client": hn_api_subsample_client.configured({"sample_rate": 10}),
}


DEFAULT_PARTITION_RESOURCE_CONFIG = {
    "partition_start": {"config": "2020-12-30 00:00:00"},
    "partition_end": {"config": "2020-12-30 01:00:00"},
}

DOWNLOAD_TAGS = {
    "dagster-k8s/config": {
        "container_config": {
            "resources": {
                "requests": {"cpu": "500m", "memory": "2Gi"},
            }
        },
    }
}


@graph(
    description="#### Owners:\n"
    "schrockn@elementl.com, cat@elementl.com\n "
    "#### About\n"
    "Downloads all items from the HN API for a given day, "
    "splits the items into stories and comment types using Spark, and uploads filtered items to "
    "the corresponding stories or comments Snowflake table",
)
def hacker_news_api_download():
    items = download_items(id_range_for_time())
    build_comments(items)
    build_stories(items)


@hourly_partitioned_config(start_date=datetime(2020, 12, 1))
def hourly_download_config(start: datetime, end: datetime):
    return {
        "resources": {
            "partition_start": {"config": start.strftime("%Y-%m-%d %H:%M:%S")},
            "partition_end": {"config": end.strftime("%Y-%m-%d %H:%M:%S")},
        }
    }


download_prod_job = hacker_news_api_download.to_job(
    resource_defs=DOWNLOAD_RESOURCES_PROD,
    tags=DOWNLOAD_TAGS,
    config=hourly_download_config,
)


download_staging_job = hacker_news_api_download.to_job(
    resource_defs=DOWNLOAD_RESOURCES_STAGING,
    tags=DOWNLOAD_TAGS,
    config=hourly_download_config,
)
