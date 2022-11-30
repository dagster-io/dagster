# isort: skip_file
# pylint: disable=unused-variable


def scope_define_instance():
    # start_define_dbt_cloud_instance
    from dagster_dbt import dbt_cloud_resource

    dbt_cloud_instance = dbt_cloud_resource.configured(
        {
            "auth_token": {"env": "DBT_CLOUD_API_TOKEN"},
            "account_id": {"env": "DBT_CLOUD_ACCOUNT_ID"},
        }
    )
    # end_define_dbt_cloud_instance


def scope_load_assets_from_dbt_cloud_job():
    from dagster_dbt import dbt_cloud_resource

    dbt_cloud_instance = dbt_cloud_resource.configured(
        {
            "auth_token": {"env": "DBT_CLOUD_API_TOKEN"},
            "account_id": {"env": "DBT_CLOUD_ACCOUNT_ID"},
        }
    )
    # start_load_assets_from_dbt_cloud_job
    from dagster_dbt import load_assets_from_dbt_cloud_job

    # Use the dbt_cloud_instance resource we defined in Step 1, and the job_id from Prerequisites
    dbt_cloud_assets = load_assets_from_dbt_cloud_job(
        dbt_cloud=dbt_cloud_instance,
        job_id=33333,
    )
    # end_load_assets_from_dbt_cloud_job


def scope_schedule_dbt_cloud_assets():
    dbt_cloud_assets = []
    # start_schedule_dbt_cloud_assets
    from dagster import ScheduleDefinition, define_asset_job, repository, AssetSelection

    # Materialize all assets in the repository
    run_everything_job = define_asset_job("run_everything_job", AssetSelection.all())

    @repository
    def my_repo():
        return [
            # Use the dbt_cloud_assets defined in Step 2
            dbt_cloud_assets,
            ScheduleDefinition(
                job=run_everything_job,
                cron_schedule="@daily",
            ),
        ]

    # end_schedule_dbt_cloud_assets
