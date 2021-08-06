from dagster.core.asset_defs import asset
from hacker_news_assets.resources.parquet_pointer import ParquetPointer
from hacker_news_assets.solids.download_items import HN_ACTION_SCHEMA


@asset(io_manager_key="db_io_manager")
def comments(comments_lake: str) -> ParquetPointer:
    return ParquetPointer(comments_lake, HN_ACTION_SCHEMA)


@asset(io_manager_key="db_io_manager")
def stories(stories_lake: str) -> ParquetPointer:
    return ParquetPointer(stories_lake, HN_ACTION_SCHEMA)
