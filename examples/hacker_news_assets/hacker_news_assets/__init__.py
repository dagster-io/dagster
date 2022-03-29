from hacker_news_assets.assets.activity_analytics import activity_analytics_assets
from hacker_news_assets.assets.core import core_assets
from hacker_news_assets.assets.recommender import recommender_assets
from hacker_news_assets.resources import RESOURCES_LOCAL, RESOURCES_PROD, RESOURCES_STAGING

from dagster import ScheduleDefinition, repository

all_assets = core_assets + activity_analytics_assets + recommender_assets


@repository
def local():
    return [AssetGroup(all_assets, resource_defs=RESOURCES_LOCAL)]


@repository
def activity_analytics():
    return [
        activity_analytics_asset_group,
        ScheduleDefinition(
            job=activity_analytics_asset_group.build_job(
                "daily_stats_job",
                selection=["comment_daily_stats", "story_daily_stats", "activity_daily_stats"],
            ),
            cron_schedule="0 0 * * *",
        ),
    ]


@repository
def recommender():
    return [recommender_asset_group]
