from dagster import AssetSelection, build_schedule_from_partitioned_job, define_asset_job

from .assets import ACTIVITY_ANALYTICS, CORE, RECOMMENDER
from .partitions import hourly_partitions
from .sensors import make_hn_tables_updated_sensor

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
