from dagster import Output, asset
from pandas import DataFrame
from pyspark.sql import DataFrame as SparkDF
from pyspark.sql.types import (
    ArrayType,
    DoubleType,
    LongType,
    StringType,
    StructField,
    StructType,
)

from project_fully_featured.partitions import hourly_partitions
from project_fully_featured.resources.hn_resource import HNClient

from .id_range_for_time import id_range_for_time

HN_ITEMS_SCHEMA = StructType(
    [
        StructField("id", LongType()),
        StructField("parent", DoubleType()),
        StructField("time", LongType()),
        StructField("type", StringType()),
        StructField("by", StringType()),
        StructField("text", StringType()),
        StructField("kids", ArrayType(LongType())),
        StructField("score", DoubleType()),
        StructField("title", StringType()),
        StructField("descendants", DoubleType()),
        StructField("url", StringType()),
    ]
)

ITEM_FIELD_NAMES = [field.name for field in HN_ITEMS_SCHEMA.fields]


@asset(
    io_manager_key="parquet_io_manager",
    partitions_def=hourly_partitions,
    key_prefix=["s3", "core"],
)
def items(context, hn_client: HNClient) -> Output[DataFrame]:
    """Items from the Hacker News API: each is a story or a comment on a story."""
    (start_id, end_id), item_range_metadata = id_range_for_time(context, hn_client)

    context.log.info(f"Downloading range {start_id} up to {end_id}: {end_id - start_id} items.")

    rows = []
    for item_id in range(start_id, end_id):
        rows.append(hn_client.fetch_item_by_id(item_id))
        if len(rows) % 100 == 0:
            context.log.info(f"Downloaded {len(rows)} items!")

    non_none_rows = [row for row in rows if row is not None]
    result = DataFrame(non_none_rows, columns=ITEM_FIELD_NAMES).drop_duplicates(subset=["id"])
    result.rename(columns={"by": "user_id"}, inplace=True)

    return Output(
        result,
        metadata={
            "Non-empty items": len(non_none_rows),
            "Empty items": rows.count(None),
            **item_range_metadata,
        },
    )


@asset(
    io_manager_key="warehouse_io_manager",
    partitions_def=hourly_partitions,
    key_prefix=["snowflake", "core"],
)
def comments(items: SparkDF) -> SparkDF:
    return items.where(items["type"] == "comment")


@asset(
    io_manager_key="warehouse_io_manager",
    partitions_def=hourly_partitions,
    key_prefix=["snowflake", "core"],
)
def stories(items: SparkDF) -> SparkDF:
    return items.where(items["type"] == "story")
