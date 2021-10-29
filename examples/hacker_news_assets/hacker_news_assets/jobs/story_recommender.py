from dagster.core.asset_defs import build_assets_job
from hacker_news_assets.assets.comment_stories import comment_stories
from hacker_news_assets.assets.comments import comments
from hacker_news_assets.assets.stories import stories
# from hacker_news_assets.assets.recommender_model import component_top_stories, recommender_model
from hacker_news_assets.assets.user_story_matrix import user_story_matrix
# from hacker_news_assets.assets.user_top_recommended_stories import user_top_recommended_stories
from hacker_news_assets.resources.fixed_s3_pickle_io_manager import fixed_s3_pickle_io_manager
from hacker_news_assets.resources.snowflake_io_manager import snowflake_io_manager_prod

RESOURCES = {
    "io_manager": fixed_s3_pickle_io_manager.configured({"bucket": "hackernews-elementl-prod"}),
    "warehouse_io_manager": snowflake_io_manager_prod,
    "source_warehouse_io_manager": snowflake_io_manager_prod,
}

assets = [
    comment_stories,
    user_story_matrix,
    # recommender_model,
    # component_top_stories,
    # user_top_recommended_stories,
]

source_assets = [comments, stories]

story_recommender = build_assets_job(
    "story_recommender", assets=assets, source_assets=source_assets, resource_defs=RESOURCES
)
