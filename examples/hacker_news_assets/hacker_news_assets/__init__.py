from hacker_news_assets.activity_analytics import (
    activity_analytics_assets,
    activity_analytics_job_spec,
    activity_analytics_assets_sensor,
    dbt_prod_resource,
    dbt_staging_resource,
)
from hacker_news_assets.core import core_assets, core_assets_schedule, core_job_spec
from hacker_news_assets.recommender import (
    recommender_assets,
    recommender_assets_sensor,
    recommender_job_spec,
)

from dagster import repository

from .sensors.slack_on_failure_sensor import make_slack_on_failure_sensor
from hacker_news_assets.resources import RESOURCES_LOCAL, RESOURCES_PROD, RESOURCES_STAGING

all_assets = activity_analytics_assets + recommender_assets + core_assets

sensors = [activity_analytics_assets_sensor, recommender_assets_sensor]
job_specs = [activity_analytics_job_spec, core_job_spec, recommender_job_spec]


@repository
def prod():
    return [
        with_resources(all_assets, resource_defs={**RESOURCES_PROD, "dbt": dbt_prod_resource}),
        sensors,
        job_specs,
        make_slack_on_failure_sensor(base_url="my_dagit_url"),
    ]


@repository
def staging():
    return [
        with_resources(all_assets, resource_defs={**RESOURCES_STAGING, "dbt": dbt_prod_resource}),
        sensors,
        job_specs,
        make_slack_on_failure_sensor(base_url="my_dagit_url"),
    ]


@repository
def local():
    return [
        with_resources(all_assets, resource_defs={**RESOURCES_LOCAL, "dbt": dbt_prod_resource}),
        job_specs,
    ]
