from typing import Tuple

from dagster import AssetKey, ExpectationResult, Out, Output
from dagster.core.asset_defs import asset, multi_asset
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

HN_ACTION_SCHEMA = StructType(
    [
        StructField("deleted", BooleanType()),
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


@asset(
    io_manager_key="parquet_io_manager",
    required_resource_keys={"hn_client"},
    description="Downloads all of the items for the id range passed in as input and creates a DataFrame with all the entries.",
)
def items(context, id_range_for_time: Tuple[int, int]) -> Output:
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


@multi_asset(
    outs={
        "comments": Out(
            SparkDF,
            io_manager_key="parquet_io_manager",
            asset_key=AssetKey("comments_lake"),
        ),
        "stories": Out(
            SparkDF,
            io_manager_key="parquet_io_manager",
            asset_key=AssetKey("stories_lake"),
        ),
    },
    required_resource_keys={"pyspark"},
    description="Split raw the DataFrame by the 'type' column.",
)
def comments_and_stories_lake(context, items: SparkDF):  # pylint: disable=redefined-outer-name
    expected_df = context.resources.pyspark.spark_session.createDataFrame([], HN_ACTION_SCHEMA)
    # Schema validation
    yield ExpectationResult(
        success=set(items.schema) == set(expected_df.schema),
        label="hn_data_schema_check",
        description="Check if the source schema is expected",
        metadata={
            "Expected data schema": expected_df._jdf.schema().treeString(),  # type: ignore # pylint: disable=protected-access
            "Actual data schema": items._jdf.schema().treeString(),  # type: ignore # pylint: disable=protected-access
        },
    )

    # Split data based on the values in the 'type' column
    type_values = items.select("type").distinct().rdd.flatMap(lambda x: x).collect()
    comment_df = items.where(items["type"] == "comment")
    story_df = items.where(items["type"] == "story")

    yield ExpectationResult(
        success=comment_df.count() > 0 and story_df.count() > 0,
        label="hn_data_split_types_check",
        description="Expect the hacker news data has at least 1 'comment' entry and at least 1 'story' entry.",
        metadata={
            "number of raw rows": items.count(),
            "number of comment rows": comment_df.count(),
            "number of story rows": story_df.count(),
            "Unique values in the 'type' column": (", ").join(type_values),
        },
    )

    yield Output(comment_df, "comments")
    yield Output(story_df, "stories")
