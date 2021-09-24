from dagster import AssetKey, InputDefinition, OutputDefinition, solid
from pyspark.sql import DataFrame
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

ITEM_FIELD_NAMES = [field.name for field in HN_ITEMS_SCHEMA.fields]


@solid(
    input_defs=[InputDefinition("items", asset_key=AssetKey("items"))],
    output_defs=[
        OutputDefinition(
            io_manager_key="warehouse_io_manager",
            asset_key=AssetKey("comments"),
        )
    ],
)
def build_comments(context, items: DataFrame) -> DataFrame:
    """Comments posted on Hacker News stories"""
    context.log.info(str(items.schema))
    return items.where(items["type"] == "comment").select(ITEM_FIELD_NAMES)
