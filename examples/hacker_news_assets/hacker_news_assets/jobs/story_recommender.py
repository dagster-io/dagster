from dagster.core.asset_defs import build_assets_job
from hacker_news_assets.assets.comment_stories import comment_stories
from hacker_news_assets.assets.items import comments, stories
from hacker_news_assets.assets.recommender_model import component_top_stories, recommender_model
from hacker_news_assets.assets.user_story_matrix import user_story_matrix
from hacker_news_assets.assets.user_top_recommended_stories import user_top_recommended_stories
from hacker_news_assets.resources import RESOURCES_PROD, RESOURCES_STAGING

assets = [
    comment_stories,
    user_story_matrix,
    recommender_model,
    component_top_stories,
    user_top_recommended_stories,
]

source_assets = [comments, stories]

from ..asset_collection import asset_collection

asset_collection.build_asset_job(subset="comment_stories*")
