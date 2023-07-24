# ruff: isort: skip_file


def scope_load_assets_from_dbt_project():
    # start_load_assets_from_dbt_project
    from dagster_dbt import load_assets_from_dbt_project

    dbt_assets = load_assets_from_dbt_project(project_dir="path/to/dbt/project")
    # end_load_assets_from_dbt_project


def scope_load_assets_from_dbt_manifest():
    # start_load_assets_from_dbt_manifest
    import json

    from dagster_dbt import load_assets_from_dbt_manifest

    with open("path/to/dbt/manifest.json") as f:
        manifest_json = json.load(f)

    dbt_assets = load_assets_from_dbt_manifest(manifest_json)
    # end_load_assets_from_dbt_manifest


def scope_dbt_cli_resource_config():
    # start_dbt_cli_resource
    import os

    from dagster_dbt import DbtCli, load_assets_from_dbt_project

    from dagster import Definitions

    DBT_PROJECT_PATH = "path/to/dbt_project"
    DBT_TARGET = "hive" if os.getenv("EXECUTION_ENV") == "prod" else "duckdb"

    defs = Definitions(
        assets=load_assets_from_dbt_project(DBT_PROJECT_PATH),
        resources={"dbt": DbtCli(project_dir=DBT_PROJECT_PATH, target=DBT_TARGET)},
    )
    # end_dbt_cli_resource


def scope_schedule_assets_dbt_only(my_dbt_assets):
    # start_schedule_assets_dbt_only
    from dagster_dbt import build_schedule_from_dbt_selection

    daily_dbt_assets_schedule = build_schedule_from_dbt_selection(
        [my_dbt_assets],
        job_name="daily_dbt_models",
        cron_schedule="@daily",
        dbt_select="tag:daily",
    )
    # end_schedule_assets_dbt_only


def scope_schedule_assets_dbt_and_downstream(my_dbt_assets):
    # start_schedule_assets_dbt_downstream
    from dagster import define_asset_job, ScheduleDefinition
    from dagster_dbt import build_dbt_asset_selection

    # selects all models tagged with "daily", and all their downstream asset dependencies
    daily_selection = build_dbt_asset_selection(
        [my_dbt_assets], dbt_select="tag:daily"
    ).downstream()

    daily_dbt_assets_and_downstream_schedule = ScheduleDefinition(
        job=define_asset_job("daily_assets", selection=daily_selection),
        cron_schedule="@daily",
    )

    # end_schedule_assets_dbt_downstream


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


def scope_upstream_asset():
    from dagster import asset

    # start_upstream_asset
    @asset(key_prefix="jaffle_shop")
    def orders():
        return ...

    # end_upstream_asset


def scope_input_manager():
    # start_input_manager
    import pandas as pd

    from dagster import ConfigurableIOManager

    class PandasIOManager(ConfigurableIOManager):
        connection_str: str

        def handle_output(self, context, obj):
            # dbt handles outputs for us
            pass

        def load_input(self, context) -> pd.DataFrame:
            """Load the contents of a table as a pandas DataFrame."""
            table_name = context.asset_key.path[-1]
            return pd.read_sql(f"SELECT * FROM {table_name}", con=self.connection_str)

    # end_input_manager


def scope_input_manager_resources():
    class PandasIOManager:
        def __init__(self, connection_str: str):
            pass

    # start_input_manager_resources
    from dagster_dbt import DbtCli, load_assets_from_dbt_project

    from dagster import Definitions

    defs = Definitions(
        assets=load_assets_from_dbt_project(...),
        resources={
            "dbt": DbtCli(project_dir="path/to/dbt_project"),
            "pandas_df_manager": PandasIOManager(connection_str=...),
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
