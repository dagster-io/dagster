# ruff: isort: skip_file

MANIFEST_PATH = ""


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

    from dagster_dbt import DbtCliResource, load_assets_from_dbt_project

    from dagster import Definitions

    DBT_PROJECT_PATH = "path/to/dbt_project"
    DBT_TARGET = "hive" if os.getenv("EXECUTION_ENV") == "prod" else "duckdb"

    defs = Definitions(
        assets=load_assets_from_dbt_project(DBT_PROJECT_PATH),
        resources={
            "dbt": DbtCliResource(project_dir=DBT_PROJECT_PATH, target=DBT_TARGET)
        },
    )
    # end_dbt_cli_resource


def scope_schedule_assets(dbt_assets):
    # start_schedule_assets
    from dagster import ScheduleDefinition, define_asset_job, Definitions

    run_everything_job = define_asset_job("run_everything", selection="*")

    # only `order_stats` and its children
    run_something_job = define_asset_job("run_something", selection="order_stats*")

    defs = Definitions(
        assets=dbt_assets,
        schedules=[
            ScheduleDefinition(
                job=run_something_job,
                cron_schedule="@daily",
            ),
            ScheduleDefinition(
                job=run_everything_job,
                cron_schedule="@weekly",
            ),
        ],
    )

    # end_schedule_assets


def scope_downstream_asset():
    from dagster import OpExecutionContext, DbtCliResource
    from dagster_dbt import dbt_assets

    @dbt_assets(manifest=MANIFEST_PATH)
    def my_dbt_assets(context: OpExecutionContext, dbt: DbtCliResource):
        ...

    # start_downstream_asset
    from dagster_dbt import get_asset_key_for_model
    from dagster import asset

    @asset(deps=[get_asset_key_for_model([my_dbt_assets], "my_dbt_model")])
    def my_downstream_asset():
        ...

    # end_downstream_asset_pandas_df_manager


def scope_downstream_asset_pandas_df_manager():
    from dagster import OpExecutionContext, DbtCliResource
    from dagster_dbt import dbt_assets

    @dbt_assets(manifest=MANIFEST_PATH)
    def my_dbt_assets(context: OpExecutionContext, dbt: DbtCliResource):
        ...

    # start_downstream_asset_pandas_df_manager
    from dagster_dbt import get_asset_key_for_model
    from dagster import AssetIn, asset

    @asset(
        ins={
            "my_dbt_model": AssetIn(
                input_manager_key="pandas_df_manager",
                key=get_asset_key_for_model([my_dbt_assets], "my_dbt_model"),
            )
        },
    )
    def my_downstream_asset(my_dbt_model):
        # my_dbt_model is a Pandas dataframe
        return my_dbt_model.where(foo="bar")

    # end_downstream_asset_pandas_df_manager


def scope_upstream_asset():
    # start_upstream_asset
    from dagster import asset, OpExecutionContext
    from dagster_dbt import DbtCliResource, get_asset_key_for_source, dbt_assets

    @dbt_assets(manifest=MANIFEST_PATH)
    def my_dbt_assets(context: OpExecutionContext, dbt: DbtCliResource):
        ...

    @asset(key=get_asset_key_for_source([my_dbt_assets], "jaffle_shop"))
    def orders():
        return ...

    # end_upstream_asset


def scope_upstream_multi_asset():
    from dagster import OpExecutionContext
    from dagster_dbt import DbtCliResource, dbt_assets

    @dbt_assets(manifest=MANIFEST_PATH)
    def my_dbt_assets(context: OpExecutionContext, dbt: DbtCliResource):
        ...

    # start_upstream_multi_asset
    from dagster import multi_asset, AssetOut, Output
    from dagster_dbt import get_asset_keys_by_output_name_for_source

    @multi_asset(
        outs={
            name: AssetOut(key=asset_key)
            for name, asset_key in get_asset_keys_by_output_name_for_source(
                [my_dbt_assets], "jaffle_shop"
            ).items()
        }
    )
    def jaffle_shop(context):
        output_names = list(context.selected_output_names)
        yield Output(value=..., output_name=output_names[0])
        yield Output(value=..., output_name=output_names[1])

    # end_upstream_multi_asset


def scope_existing_asset():
    # start_upstream_dagster_asset
    from dagster import asset

    @asset
    def upstream():
        ...

    # end_upstream_dagster_asset


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
    from dagster_dbt import DbtCliResource, load_assets_from_dbt_project

    from dagster import Definitions

    defs = Definitions(
        assets=load_assets_from_dbt_project(...),
        resources={
            "dbt": DbtCliResource(project_dir="path/to/dbt_project"),
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
