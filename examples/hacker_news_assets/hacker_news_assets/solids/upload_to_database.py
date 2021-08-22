from dagster.core.asset_defs import table
from hacker_news_assets.resources.parquet_pointer import ParquetPointer
from hacker_news_assets.solids.download_items import HN_ITEMS_COLUMNS, HN_ITEMS_SCHEMA


@table(io_manager_key="warehouse_io_manager", columns=HN_ITEMS_COLUMNS)
def comments(comments_lake: str) -> ParquetPointer:
    """Comments posted on Hacker News stories"""
    return ParquetPointer(comments_lake, HN_ITEMS_SCHEMA)


@table(io_manager_key="warehouse_io_manager", columns=HN_ITEMS_COLUMNS)
def stories(stories_lake: str) -> ParquetPointer:
    """"Stories posted on Hacker News"""
    return ParquetPointer(stories_lake, HN_ITEMS_SCHEMA)
