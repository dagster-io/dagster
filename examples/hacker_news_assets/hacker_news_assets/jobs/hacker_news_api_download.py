from dagster.core.asset_defs import build_assets_job
from dagster.seven.temp_dir import get_system_temp_directory
from hacker_news_assets.assets.comments import comments
from hacker_news_assets.assets.items import items
from hacker_news_assets.assets.stories import stories
from hacker_news_assets.resources.hn_resource import hn_api_subsample_client
from hacker_news_assets.resources.parquet_io_manager import parquet_io_manager
from hacker_news_assets.resources.snowflake_io_manager import snowflake_io_manager_prod

RESOURCES = {
    "parquet_io_manager": parquet_io_manager.configured({"base_path": get_system_temp_directory()}),
    "warehouse_io_manager": snowflake_io_manager_prod,
    "hn_client": hn_api_subsample_client.configured({"sample_rate": 10}),
}

# assets = [items, comments, stories]
assets = [items]

hacker_news_api_download = build_assets_job(
    "hacker_news_api_download", assets=assets, resource_defs=RESOURCES
)
