# isort: skip_file
# pylint: disable=unused-variable


def scope_load_assets_from_airbyte_project():
    # start_load_assets_from_airbyte_project
    from dagster_airbyte import load_assets_from_airbyte_project

    airbyte_assets = load_assets_from_airbyte_project(project_dir="path/to/airbyte/project")
    # end_load_assets_from_airbyte_project


def scope_load_assets_from_airbyte_instance():
    # start_load_assets_from_airbyte_instance
    from dagster_airbyte import airbyte_resource, load_assets_from_airbyte_instance

    airbyte_instance = airbyte_resource.configured(
        {
            "host": "localhost",
            "port": "8000",
        }
    )
    airbyte_assets = load_assets_from_airbyte_instance(airbyte_instance)
    # end_load_assets_from_airbyte_instance


def scope_airbyte_project_config():
    # start_airbyte_project_config
    from dagster_airbyte import airbyte_resource, load_assets_from_airbyte_project

    from dagster import with_resources

    airbyte_assets = with_resources(
        load_assets_from_airbyte_project(project_dir="path/to/airbyte/project"),
        {
            "airbyte": airbyte_resource.configured(
                {
                    "host": "localhost",
                    "port": "8000",
                }
            )
        },
    )
    # end_airbyte_project_config


def scope_schedule_assets():
    airbyte_assets = []
    # start_schedule_assets
    from dagster import ScheduleDefinition, define_asset_job, repository

    run_everything_job = define_asset_job("run_everything", selection="*")

    # only my_model and its children
    run_something_job = define_asset_job("run_something", selection="my_connection*")

    @repository
    def my_repo():
        return [
            airbyte_assets,
            ScheduleDefinition(
                job=run_something_job,
                cron_schedule="@daily",
            ),
            ScheduleDefinition(
                job=run_everything_job,
                cron_schedule="@weekly",
            ),
        ]

    # end_schedule_assets
