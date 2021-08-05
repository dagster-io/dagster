from dagster import AssetKey, fs_io_manager
from dagster.core.asset_defs import SourceAsset, build_assets_job
from hacker_news.resources.fixed_s3_pickle_io_manager import fixed_s3_pickle_io_manager
from hacker_news.resources.snowflake_io_manager import snowflake_io_manager
from hacker_news.solids.comment_stories import comment_stories
from hacker_news.solids.recommender_model import component_top_stories, recommender_model
from hacker_news.solids.user_story_matrix import user_story_matrix
from hacker_news.solids.user_top_recommended_stories import user_top_recommended_stories

snowflake_manager = snowflake_io_manager.configured(
    {
        "account": {"env": "SNOWFLAKE_ACCOUNT"},
        "user": {"env": "SNOWFLAKE_USER"},
        "password": {"env": "SNOWFLAKE_PASSWORD"},
        "database": "DEMO_DB",
        "warehouse": "TINY_WAREHOUSE",
    }
)

DEV_RESOURCES = {
    "io_manager": fs_io_manager,
    "warehouse_io_manager": fs_io_manager,
    "source_warehouse_io_manager": snowflake_manager,
}

PROD_RESOURCES = {
    "io_manager": fixed_s3_pickle_io_manager.configured({"bucket": "hackernews-elementl-prod"}),
    "warehouse_io_manager": snowflake_manager,
    "source_warehouse_io_manager": snowflake_manager,
}

assets = [
    comment_stories,
    user_story_matrix,
    recommender_model,
    component_top_stories,
    user_top_recommended_stories,
]

source_assets = [
    SourceAsset(AssetKey("comments"), io_manager_key="source_warehouse_io_manager"),
    SourceAsset(AssetKey("stories"), io_manager_key="source_warehouse_io_manager"),
]

story_recommender_dev = build_assets_job(
    "story_recommender_dev", assets=assets, source_assets=source_assets, resource_defs=DEV_RESOURCES
)

story_recommender_prod = build_assets_job(
    "story_recommender_prod",
    assets=assets,
    source_assets=source_assets,
    resource_defs=PROD_RESOURCES,
)
