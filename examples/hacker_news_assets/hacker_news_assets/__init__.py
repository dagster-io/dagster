from hacker_news_assets.activity_analytics import (
    activity_analytics_definitions_local,
    activity_analytics_definitions_prod,
    activity_analytics_definitions_staging,
)
from hacker_news_assets.core import (
    core_definitions_local,
    core_definitions_prod,
    core_definitions_staging,
)
from hacker_news_assets.recommender import (
    recommender_definitions_local,
    recommender_definitions_prod,
    recommender_definitions_staging,
)

from dagster import repository

from .sensors.slack_on_failure_sensor import make_slack_on_failure_sensor


@repository
def prod():
    return [
        *core_definitions_prod,
        *recommender_definitions_prod,
        *activity_analytics_definitions_prod,
        make_slack_on_failure_sensor(base_url="my_dagit_url"),
    ]


@repository
def staging():
    return [
        *core_definitions_staging,
        *recommender_definitions_staging,
        *activity_analytics_definitions_staging,
        make_slack_on_failure_sensor(base_url="my_dagit_url"),
    ]


@repository
def local():
    return [
        *core_definitions_local,
        *recommender_definitions_local,
        *activity_analytics_definitions_local,
    ]
