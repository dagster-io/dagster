from typing import Optional

from dagster import repository, schedule_from_partitions

from .assets import build_asset_group
from .jobs.activity_stats import build_activity_stats_job
from .jobs.hacker_news_api_download import build_download_job
from .jobs.story_recommender import build_story_recommender_job
from .sensors.hn_tables_updated_sensor import make_hn_tables_updated_sensor
from .sensors.slack_on_failure_sensor import make_slack_on_failure_sensor


@repository
def hacker_news_assets(deployment_name: Optional[str]):
    asset_group = build_asset_group(deployment_name)

    return [
        build_asset_group(deployment_name),
        schedule_from_partitions(build_download_job(asset_group)),
        make_slack_on_failure_sensor(base_url="my_dagit_url.com"),
        make_hn_tables_updated_sensor(build_activity_stats_job(asset_group)),
        make_hn_tables_updated_sensor(build_story_recommender_job(asset_group)),
    ]
