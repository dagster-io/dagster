import json
import os

from dagster_dbt.asset_defs import load_assets_from_dbt_manifest
from hacker_news_assets.activity_analytics import (
    activity_analytics_assets,
    activity_analytics_assets_sensor,
)
from hacker_news_assets.core import core_assets, core_assets_schedule
from hacker_news_assets.recommender import recommender_assets, recommender_assets_sensor
from hacker_news_assets.resources import RESOURCES_LOCAL, RESOURCES_PROD, RESOURCES_STAGING

from dagster import repository, with_resources
from dagster.utils import file_relative_path

from .sensors.slack_on_failure_sensor import make_slack_on_failure_sensor

DBT_PROJECT_DIR = file_relative_path(__file__, "../dbt")
DBT_PROFILES_DIR = DBT_PROJECT_DIR + "/config"

dbt_assets = load_assets_from_dbt_manifest(
    json.load(open(os.path.join(DBT_PROJECT_DIR, "target", "manifest.json"), encoding="utf-8")),
    io_manager_key="warehouse_io_manager",
    # the schemas are already specified in dbt, so we don't need to also specify them in the key
    # prefix here
    key_prefix=["snowflake"],
)

all_assets = [*core_assets, *recommender_assets, *dbt_assets, *activity_analytics_assets]
all_jobs = [core_assets_schedule, activity_analytics_assets_sensor, recommender_assets_sensor]

resource_defs_by_deployment_name = {
    "prod": RESOURCES_PROD,
    "staging": RESOURCES_STAGING,
    "local": RESOURCES_LOCAL,
}


@repository
def repo():
    deployment_name = os.environ.get("DAGSTER_DEPLOYMENT", "local")
    resource_defs = resource_defs_by_deployment_name[deployment_name]

    definitions = [with_resources(all_assets, resource_defs), all_jobs]
    if deployment_name in ["prod", "staging"]:
        definitions.append(make_slack_on_failure_sensor(base_url="my_dagit_url"))

    return definitions
