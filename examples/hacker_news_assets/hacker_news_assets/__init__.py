from hacker_news_assets.activity_analytics import activity_analytics_definitions
from hacker_news_assets.core import core_definitions
from hacker_news_assets.recommender import recommender_definitions
from hacker_news_assets.resources import get_resource_set_for_deployment

from dagster import repository


@repository
def repo(deployment_name: str):
    return [
        core_definitions,
        recommender_definitions,
        activity_analytics_definitions,
        get_resource_set_for_deployment(deployment_name),
    ]
