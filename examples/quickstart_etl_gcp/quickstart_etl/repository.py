from dagster import (
    ScheduleDefinition,
    define_asset_job,
    load_assets_from_package_module,
    repository,
    with_resources,
)

from . import assets

from dagster_gcp import gcs_pickle_io_manager, gcs_resource, bigquery_resource

daily_metrics_report_schedule = ScheduleDefinition(
    job=define_asset_job(name="metrics_report_job"), cron_schedule="0 0 * * *"
)


@repository
def quickstart_etl_gcp():
    return [
        with_resources(
            *load_assets_from_package_module(assets),
            resource_defs={
                # "io_manager": gcs_pickle_io_manager.configured(
                #     {"gcs_bucket": "my-cool-bucket", "gcs_prefix": "my-cool-prefix"}
                # ),
                # "gcs": gcs_resource,
                # "bigquery": bigquery_resource,
            },
        ),
        daily_metrics_report_schedule,
    ]
