from typing import List, Tuple

from dagster import ExpectationResult, Output, OutputDefinition, RetryRequested, solid
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


@solid(
    output_defs=[
        OutputDefinition(name="items", io_manager_key="parquet_io_manager", dagster_type=DataFrame)
    ],
    required_resource_keys={"hn_client"},
    description="Downloads all of the items for the id range passed in as input and creates a DataFrame with all the entries.",
)
def download_items(context, id_range: Tuple[int, int]) -> Output:
    """
    Downloads all of the items for the id range passed in as input and creates a DataFrame with
    all the entries.
    """
    start_id, end_id = id_range

    context.log.info(f"Downloading range {start_id} up to {end_id}: {end_id - start_id} items.")

    rows = []
    for item_id in range(start_id, end_id):
        rows.append(context.resources.hn_client.fetch_item_by_id(item_id))
        if len(rows) % 100 == 0:
            context.log.info(f"Downloaded {len(rows)} items!")

    non_none_rows = [row for row in rows if row is not None]

    return Output(
        DataFrame(non_none_rows).drop_duplicates(subset=["id"]),
        "items",
        metadata={"Non-empty items": len(non_none_rows), "Empty items": rows.count(None)},
    )


@solid(
    required_resource_keys={"hn_client"},
    description="Downloads all of the items for the id range passed in as input and return the List of items.",
)
def dynamic_download_items(context, id_range: Tuple[int, int]) -> List[dict]:
    start_id, end_id = id_range

    context.log.info(f"Downloading range {start_id} up to {end_id}: {end_id - start_id} items.")
    try:
        return [
            context.resources.hn_client.fetch_item_by_id(item_id)
            for item_id in range(start_id, end_id)
        ]
    except Exception as e:
        raise RetryRequested(max_retries=3) from e


@solid(
    output_defs=[OutputDefinition(name="items", io_manager_key="parquet_io_manager")],
    description="Creates a DataFrame with all the entries from combining batch of items.",
)
def join_items(_, item_batches: List[List[dict]]) -> DataFrame:
    return DataFrame(item for items in item_batches for item in items)


@solid(
    output_defs=[
        OutputDefinition(SparkDF, "comments", io_manager_key="parquet_io_manager"),
        OutputDefinition(SparkDF, "stories", io_manager_key="parquet_io_manager"),
    ],
    required_resource_keys={"pyspark"},
    description="Split raw the DataFrame by the 'type' column.",
)
def split_types(context, raw_df: SparkDF):
    expected_df = context.resources.pyspark.spark_session.createDataFrame([], HN_ACTION_SCHEMA)
    # Schema validation
    yield ExpectationResult(
        success=set(raw_df.schema) == set(expected_df.schema),
        label="hn_data_schema_check",
        description="Check if the source schema is expected",
        metadata={
            "Expected data schema": expected_df._jdf.schema().treeString(),  # type: ignore # pylint: disable=protected-access
            "Actual data schema": raw_df._jdf.schema().treeString(),  # type: ignore # pylint: disable=protected-access
        },
    )

    # Split data based on the values in the 'type' column
    type_values = raw_df.select("type").distinct().rdd.flatMap(lambda x: x).collect()
    comment_df = raw_df.where(raw_df["type"] == "comment")
    story_df = raw_df.where(raw_df["type"] == "story")

    yield ExpectationResult(
        success=comment_df.count() > 0 and story_df.count() > 0,
        label="hn_data_split_types_check",
        description="Expect the hacker news data has at least 1 'comment' entry and at least 1 'story' entry.",
        metadata={
            "number of raw rows": raw_df.count(),
            "number of comment rows": comment_df.count(),
            "number of story rows": story_df.count(),
            "Unique values in the 'type' column": (", ").join(type_values),
        },
    )

    yield Output(comment_df, "comments")
    yield Output(story_df, "stories")
