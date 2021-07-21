import os

from dagster import (
    ModeDefinition,
    PresetDefinition,
    ResourceDefinition,
    fs_io_manager,
    mem_io_manager,
    pipeline,
)
from dagster.seven.temp_dir import get_system_temp_directory
from dagster_aws.s3 import s3_pickle_io_manager, s3_resource
from dagster_pyspark import pyspark_resource
from dagster_slack import slack_resource
from hacker_news.hooks.slack_hooks import slack_on_success
from hacker_news.resources.hn_resource import hn_api_subsample_client, hn_snapshot_client
from hacker_news.resources.parquet_io_manager import partitioned_parquet_io_manager
from hacker_news.resources.snowflake_io_manager import time_partitioned_snowflake_io_manager
from hacker_news.solids.download_items import (
    HN_ACTION_SCHEMA,
    download_items,
    dynamic_download_items,
    join_items,
    split_types,
)
from hacker_news.solids.id_range_for_time import dynamic_id_ranges_for_time, id_range_for_time
from hacker_news.solids.upload_to_database import make_upload_to_database_solid

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


MODE_TEST = ModeDefinition(
    name="test_local_data",
    description="This mode queries snapshotted HN data and does all writes locally.",
    resource_defs={
        "io_manager": fs_io_manager,
        "partition_start": ResourceDefinition.string_resource(),
        "partition_end": ResourceDefinition.string_resource(),
        "parquet_io_manager": partitioned_parquet_io_manager,
        "db_io_manager": mem_io_manager,
        "pyspark": pyspark_resource,
        "hn_client": hn_snapshot_client,
        "slack": ResourceDefinition.mock_resource(),
        "base_url": ResourceDefinition.hardcoded_resource("http://localhost:3000", "Dagit URL"),
    },
)


MODE_LOCAL = ModeDefinition(
    name="local_live_data",
    description=(
        "This mode queries live HN data but does all writes locally. "
        "It is meant to be used on a local machine"
    ),
    resource_defs={
        "io_manager": fs_io_manager,
        "partition_start": ResourceDefinition.string_resource(),
        "partition_end": ResourceDefinition.string_resource(),
        "parquet_io_manager": partitioned_parquet_io_manager.configured(
            {"base_path": get_system_temp_directory()}
        ),
        "db_io_manager": fs_io_manager,
        "pyspark": pyspark_resource,
        "hn_client": hn_api_subsample_client.configured({"sample_rate": 10}),
        "slack": ResourceDefinition.mock_resource(),
        "base_url": ResourceDefinition.hardcoded_resource("http://localhost:3000", "Dagit URL"),
    },
)


MODE_STAGING = ModeDefinition(
    name="staging_live_data",
    description=(
        "This mode queries live HN data and writes to a staging S3 bucket. "
        "Intended for use in the staging environment."
    ),
    resource_defs={
        "io_manager": s3_pickle_io_manager.configured({"s3_bucket": "hackernews-elementl-dev"}),
        "s3": s3_resource,
        "partition_start": ResourceDefinition.string_resource(),
        "partition_end": ResourceDefinition.string_resource(),
        "parquet_io_manager": partitioned_parquet_io_manager.configured(
            {"base_path": "s3://hackernews-elementl-dev"}
        ),
        "db_io_manager": time_partitioned_snowflake_io_manager.configured(SNOWFLAKE_CONF),
        "pyspark": pyspark_resource.configured(S3_SPARK_CONF),
        "hn_client": hn_api_subsample_client.configured({"sample_rate": 10}),
        "slack": ResourceDefinition.mock_resource(),
        "base_url": ResourceDefinition.hardcoded_resource("http://demo.elementl.dev", "Dagit URL"),
    },
)


MODE_PROD = ModeDefinition(
    name="prod",
    description=(
        "This mode queries live HN data and writes to a prod S3 bucket."
        "Intended for use in production."
    ),
    resource_defs={
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
        "slack": slack_resource.configured({"token": {"env": "SLACK_DAGSTER_ETL_BOT_TOKEN"}}),
        "base_url": ResourceDefinition.hardcoded_resource(
            "https://demo.elementl.show", "Dagit URL"
        ),
    },
)

download_pipeline_properties = {
    "description": "#### Owners:\n"
    "schrockn@elementl.com, cat@elementl.com\n "
    "#### About\n"
    "This pipeline downloads all items from the HN API for a given day, "
    "splits the items into stories and comment types using Spark, and uploads filtered items to "
    "the corresponding stories or comments Snowflake table",
    "mode_defs": [
        MODE_TEST,
        MODE_LOCAL,
        MODE_STAGING,
        MODE_PROD,
    ],
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

DEFAULT_PARTITION_RESOURCE_CONFIG = {
    "partition_start": {"config": "2020-12-30 00:00:00"},
    "partition_end": {"config": "2020-12-30 01:00:00"},
}

PRESET_TEST = PresetDefinition(
    name="test_local_data",
    run_config={
        "resources": dict(
            parquet_io_manager={"config": {"base_path": get_system_temp_directory()}},
            **DEFAULT_PARTITION_RESOURCE_CONFIG,
        ),
    },
    mode="test_local_data",
)

PRESET_TEST_DYNAMIC = PresetDefinition(
    name="test_local_data",
    run_config={
        "solids": {
            "dynamic_id_ranges_for_time": {
                "config": {
                    "batch_size": 100,
                }
            },
        },
        "resources": dict(
            parquet_io_manager={"config": {"base_path": get_system_temp_directory()}},
            **DEFAULT_PARTITION_RESOURCE_CONFIG,
        ),
    },
    mode="test_local_data",
)

# Here, we generate solids by use of the make_upload_to_database_solid factory method. This pattern
# is used to create solids with similar properties (in this case, they perform the same exact
# function, only differing in what table name they attach to their Output's metadata), without having
# to duplicate our code.
upload_comments = make_upload_to_database_solid(
    table="hackernews.comments",
    schema=HN_ACTION_SCHEMA,
)
upload_stories = make_upload_to_database_solid(
    table="hackernews.stories",
    schema=HN_ACTION_SCHEMA,
)


@pipeline(**download_pipeline_properties, preset_defs=[PRESET_TEST])
def download_pipeline():
    comments, stories = split_types(
        download_items.with_hooks({slack_on_success})(id_range_for_time())
    )
    upload_comments(comments)
    upload_stories(stories)


# This pipeline does the same thing as the the regular download_pipeline, but with the map / collect
# pattern. This allows the download operation to be parallelized.
@pipeline(**download_pipeline_properties, preset_defs=[PRESET_TEST_DYNAMIC])
def dynamic_download_pipeline():
    ranges = dynamic_id_ranges_for_time()
    items = ranges.map(dynamic_download_items)  # pylint: disable=no-member
    raw_df = join_items.with_hooks({slack_on_success})(items.collect())
    comments, stories = split_types(raw_df)

    upload_comments(comments)
    upload_stories(stories)
