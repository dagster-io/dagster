# ruff: isort: skip_file
import os

from dagster_dbt import dbt_cloud_resource, load_assets_from_dbt_cloud_job

import dagster as dg


def scope_define_instance():
    # start_define_dbt_cloud_instance
    from dagster_dbt import DbtCloudClientResource
    from dagster import EnvVar

    dbt_cloud_instance = DbtCloudClientResource(
        auth_token=EnvVar("DBT_CLOUD_API_TOKEN"),
        account_id=EnvVar.int("DBT_CLOUD_ACCOUNT_ID"),
    )
    # end_define_dbt_cloud_instance

    return dbt_cloud_instance


def scope_load_assets_from_dbt_cloud_job():
    from dagster_dbt import DbtCloudClientResource
    from dagster import EnvVar

    dbt_cloud_instance = DbtCloudClientResource(
        auth_token=EnvVar("DBT_CLOUD_API_TOKEN"),
        account_id=EnvVar.int("DBT_CLOUD_ACCOUNT_ID"),
    )
    # start_load_assets_from_dbt_cloud_job
    from dagster_dbt import load_assets_from_dbt_cloud_job

    # Use the dbt_cloud_instance resource we defined in Step 1, and the job_id from Prerequisites
    dbt_cloud_assets = load_assets_from_dbt_cloud_job(
        dbt_cloud=dbt_cloud_instance,
        job_id=33333,
    )
    # end_load_assets_from_dbt_cloud_job


def scope_schedule_dbt_cloud_assets(dbt_cloud_assets):
    # start_schedule_dbt_cloud_assets
    import dagster as dg

    # Materialize all assets
    run_everything_job = dg.define_asset_job(
        "run_everything_job", dg.AssetSelection.all()
    )

    defs = dg.Definitions(
        # Use the dbt_cloud_assets defined in Step 2
        assets=[dbt_cloud_assets],
        schedules=[
            dg.ScheduleDefinition(
                job=run_everything_job,
                cron_schedule="@daily",
            ),
        ],
    )

    # end_schedule_dbt_cloud_assets
