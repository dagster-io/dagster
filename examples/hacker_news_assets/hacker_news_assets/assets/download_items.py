# pylint: disable=redefined-outer-name

from typing import Tuple

from dagster import Output
from dagster.core.asset_defs import asset
from pandas import DataFrame
from pyspark.sql import DataFrame as SparkDF
from pyspark.sql.types import (
    ArrayType,
    BooleanType,
    DoubleType,
    LongType,
    StringType,
    StructField,
    StructType,
)

HN_ITEMS_SCHEMA = StructType(
    [
        StructField("id", LongType()),
        StructField("parent", DoubleType()),
        StructField("time", LongType()),
        StructField("type", StringType()),
        StructField("by", StringType()),
        StructField("text", StringType()),
        StructField("kids", ArrayType(LongType())),
        StructField("dead", BooleanType()),
        StructField("score", DoubleType()),
        StructField("title", StringType()),
        StructField("descendants", DoubleType()),
        StructField("url", StringType()),
    ]
)

ITEM_FIELD_NAMES = [field.name for field in HN_ITEMS_SCHEMA.fields]


@asset(
    io_manager_key="parquet_io_manager",
    required_resource_keys={"hn_client"},
    description="Items from the Hacker News API: each is a story or a comment on a story.",
)
def items(context, id_range_for_time: Tuple[int, int]):
    """
    Downloads all of the items for the id range passed in as input and creates a DataFrame with
    all the entries.
    """
    start_id, end_id = id_range_for_time

    context.log.info(f"Downloading range {start_id} up to {end_id}: {end_id - start_id} items.")

    rows = []
    for item_id in range(start_id, end_id):
        rows.append(context.resources.hn_client.fetch_item_by_id(item_id))
        if len(rows) % 100 == 0:
            context.log.info(f"Downloaded {len(rows)} items!")

    non_none_rows = [row for row in rows if row is not None]

    yield Output(
        DataFrame(non_none_rows).drop_duplicates(subset=["id"]),
        metadata={"Non-empty items": len(non_none_rows), "Empty items": rows.count(None)},
    )


@asset(io_manager_key="warehouse_io_manager")
def comments(items: SparkDF) -> SparkDF:
    return items.where(items["type"] == "comment").select(ITEM_FIELD_NAMES)


@asset(io_manager_key="warehouse_io_manager")
def stories(items: SparkDF) -> SparkDF:
    return items.where(items["type"] == "stories").select(ITEM_FIELD_NAMES)
