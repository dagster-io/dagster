import os

from hacker_news_assets.assets import (
    ACTIVITY_ANALYTICS,
    CORE,
    RECOMMENDER,
    activity_analytics_assets,
    core_assets,
    dbt_assets,
    recommender_assets,
)
from hacker_news_assets.partitions import hourly_partitions
from hacker_news_assets.resources import RESOURCES_LOCAL, RESOURCES_PROD, RESOURCES_STAGING
from hacker_news_assets.sensors import make_hn_tables_updated_sensor, make_slack_on_failure_sensor

from dagster import (
    AssetSelection,
    build_schedule_from_partitioned_job,
    define_asset_job,
    repository,
    with_resources,
)

# TBD: is it a good practice to put all sensors and sensors live inside repository?
# * pros:
#       * no extra schedule and sensor layers at starter - sensors and schedules are mostly just wrappers around jobs or asset groups
#       * users can choose to separate them out once the project grows
# * cons:
#       * it'd be a lot of code "in your face" as the the repository is the main entry of a dagster
#         project.

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
