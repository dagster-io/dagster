import json
import os

from dagster_dbt.asset_defs import load_assets_from_dbt_manifest

from dagster import AssetSelection, define_asset_job, repository, with_resources
from dagster._utils import file_relative_path

from .assets import (
    ACTIVITY_ANALYTICS,
    CORE,
    RECOMMENDER,
    activity_analytics_assets,
    core_assets,
    dbt_assets,
    recommender_assets,
)
from .partitions import hourly_partitions
from .resources import RESOURCES_LOCAL, RESOURCES_PROD, RESOURCES_STAGING
from .sensors import (
    build_schedule_from_partitioned_job,
    make_hn_tables_updated_sensor,
    make_slack_on_failure_sensor,
)

DBT_PROJECT_DIR = file_relative_path(__file__, "../dbt_project")
DBT_PROFILES_DIR = DBT_PROJECT_DIR + "/config"

dbt_assets = load_assets_from_dbt_manifest(
    json.load(open(os.path.join(DBT_PROJECT_DIR, "target", "manifest.json"), encoding="utf-8")),
    io_manager_key="warehouse_io_manager",
    # the schemas are already specified in dbt, so we don't need to also specify them in the key
    # prefix here
    key_prefix=["snowflake"],
    source_key_prefix=["snowflake"],
)

all_assets = [*core_assets, *recommender_assets, *dbt_assets, *activity_analytics_assets]

activity_analytics_assets_sensor = make_hn_tables_updated_sensor(
    # selecting by group allows us to include the activity_analytics assets that are defined in dbt
    define_asset_job("activity_analytics_job", selection=AssetSelection.groups(ACTIVITY_ANALYTICS))
)

recommender_assets_sensor = make_hn_tables_updated_sensor(
    define_asset_job("story_recommender_job", selection=AssetSelection.groups(RECOMMENDER))
)

core_assets_schedule = build_schedule_from_partitioned_job(
    define_asset_job(
        "core_job",
        selection=AssetSelection.groups(CORE),
        tags={
            "dagster-k8s/config": {
                "container_config": {
                    "resources": {
                        "requests": {"cpu": "500m", "memory": "2Gi"},
                    }
                },
            }
        },
        partitions_def=hourly_partitions,
    )
)

resource_defs_by_deployment_name = {
    "prod": RESOURCES_PROD,
    "staging": RESOURCES_STAGING,
    "local": RESOURCES_LOCAL,
}


@repository
def hacker_news_repository():
    deployment_name = os.environ.get("DAGSTER_DEPLOYMENT", "local")
    resource_defs = resource_defs_by_deployment_name[deployment_name]

    definitions = [with_resources(all_assets, resource_defs), all_jobs]
    if deployment_name in ["prod", "staging"]:
        definitions.append(make_slack_on_failure_sensor(base_url="my_dagit_url"))

    return definitions
