# pylint: disable=redefined-outer-name

from dagster.core.asset_defs import asset
from hacker_news.resources.hn_resource import HNAPISubsampleClient
from pandas import DataFrame
from pyspark.sql.types import ArrayType, DoubleType, LongType, StringType, StructField, StructType

HN_ITEMS_SCHEMA = StructType(
    [
        StructField("id", LongType()),
        StructField("parent", DoubleType()),
        StructField("time", LongType()),
        StructField("type", StringType()),
        StructField("user_id", StringType()),
        StructField("text", StringType()),
        StructField("kids", ArrayType(LongType())),
        StructField("score", DoubleType()),
        StructField("title", StringType()),
        StructField("descendants", DoubleType()),
        StructField("url", StringType()),
    ]
)

ITEM_FIELD_NAMES = [field.name for field in HN_ITEMS_SCHEMA.fields]

"""

    Columns: {', '.join(ITEM_FIELD_NAMES)}
"""


@asset(
    io_manager_key="parquet_io_manager",
    description=f"""
    Items from the Hacker News API: each is a story or a comment on a story.

    The score is computed from upvotes and downvotes on the content.
    """,
)
def items(context):
    start_id, end_id = 29034340, 29034400

    hn_client = HNAPISubsampleClient(10)

    rows = []
    for item_id in range(start_id, end_id):
        rows.append(hn_client.fetch_item_by_id(item_id))
        if len(rows) % 100 == 0:
            context.log.info(f"Downloaded {len(rows)} items!")

    non_none_rows = [row for row in rows if row is not None]

    result = DataFrame(non_none_rows, columns=ITEM_FIELD_NAMES).drop_duplicates(subset=["id"])
    result.rename(columns={"by": "user_id"}, inplace=True)

    return result
