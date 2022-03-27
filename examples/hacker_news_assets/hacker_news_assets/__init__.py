from hacker_news_assets.assets.activity_analytics import activity_analytics_asset_group
from hacker_news_assets.assets.core import core_asset_group
from hacker_news_assets.assets.recommender import recommender_asset_group

from dagster import ScheduleDefinition, repository


@repository
def core():
    return [core_asset_group]


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
