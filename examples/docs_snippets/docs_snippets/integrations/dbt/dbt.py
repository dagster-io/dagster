# pylint: disable=unused-variable


def scope_load_assets_from_dbt_project():
    # start_load_assets_from_dbt_project
    from dagster_dbt import load_assets_from_dbt_project

    dbt_assets = load_assets_from_dbt_project(project_dir="path/to/dbt/project")
    # end_load_assets_from_dbt_project


def scope_load_assets_from_dbt_manifest():
    # start_load_assets_from_dbt_manifest
    import json

    from dagster_dbt import load_assets_from_dbt_manifest

    dbt_assets = load_assets_from_dbt_manifest(
        json.load("path/to/dbt/manifest.json", encoding="utf8"),
    )
    # end_load_assets_from_dbt_manifest


def scope_dbt_cli_resource_config():
    # start_dbt_cli_resource
    from dagster_dbt import dbt_cli_resource, load_assets_from_dbt_project

    from dagster import with_resources

    DBT_PROJECT_PATH = "path/to/dbt_project"

    dbt_assets = with_resources(
        load_assets_from_dbt_project(DBT_PROJECT_PATH),
        {
            "dbt": dbt_cli_resource.configured(
                {"project_dir": DBT_PROJECT_PATH},
            )
        },
    )
    # end_dbt_cli_resource


def scope_schedule_assets():
    dbt_assets = []
    # start_schedule_assets
    from dagster import ScheduleDefinition, define_asset_job, repository

    run_everything_job = define_asset_job("run_everything", selection="*")

    # only my_model and its children
    run_something_job = define_asset_job("run_something", selection="my_model*")

    @repository
    def my_repo():
        return [
            dbt_assets,
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


def scope_downstream_asset():
    from dagster import AssetIn, asset

    # start_downstream_asset
    @asset(
        ins={"my_dbt_model": AssetIn(input_manager_key="pandas_df_manager")},
    )
    def my_downstream_asset(my_dbt_model):
        # my_dbt_model is a Pandas dataframe
        return my_dbt_model.where(foo="bar")

    # end_downstream_asset


def scope_input_manager():
    # start_input_manager
    import pandas as pd

    from dagster import IOManager, io_manager

    class PandasIOManager(IOManager):
        def __init__(self, con_string: str):
            self._con = con_string

        def handle_output(self, context, obj):
            # dbt handles outputs for us
            pass

        def load_input(self, context) -> pd.DataFrame:
            """Load the contents of a table as a pandas DataFrame."""
            table_name = context.asset_key.path[-1]
            return pd.read_sql(f"SELECT * FROM {table_name}", con=self._con)

    @io_manager(config_schema={"con_string": str})
    def pandas_io_manager(context):
        return PandasIOManager(context.resource_config["con_string"])

    # end_input_manager


def scope_input_manager_resources():
    pandas_io_manager = None
    # start_input_manager_resources
    from dagster_dbt import dbt_cli_resource, load_assets_from_dbt_project

    from dagster import with_resources

    dbt_assets = with_resources(
        load_assets_from_dbt_project(...),
        {
            "dbt": dbt_cli_resource.configured(
                {"project_dir": "path/to/dbt_project"},
            ),
            "pandas_df_manager": pandas_io_manager.configured(
                {"con_string": "..."},
            ),
        },
    )
    # end_input_manager_resources


def scope_key_prefixes():
    from dagster_dbt import load_assets_from_dbt_project

    # start_key_prefix
    dbt_assets = load_assets_from_dbt_project(
        "path/to/dbt_project",
        key_prefix="snowflake",
    )
    # end_key_prefix
    # start_source_key_prefix
    dbt_assets = load_assets_from_dbt_project(
        "path/to/dbt_project",
        source_key_prefix="snowflake",
    )
    # end_source_key_prefix
