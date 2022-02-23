from dagster import AssetGroup, ScheduleDefinition, repository, asset, fs_asset_io_manager
from dagster_airbyte import airbyte_resource, build_airbyte_assets
from dagster_dbt import dbt_cli_resource, load_assets_from_dbt_project
from .constants import AIRBYTE_CONNECTION_ID, AIRBYTE_CONFIG, DBT_PROJECT_DIR, DBT_CONFIG

airbyte_assets = build_airbyte_assets(
    connection_id=AIRBYTE_CONNECTION_ID, destination_tables=["orders", "users"]
)

dbt_assets = load_assets_from_dbt_project(DBT_PROJECT_DIR)


@asset
def order_forecast_model(daily_order_summary):
    return 1


@asset
def predicted_orders(order_forecast_model):
    return 1


asset_group = AssetGroup(
    airbyte_assets + dbt_assets + [order_forecast_model, predicted_orders],
    resource_defs={
        "airbyte": airbyte_resource.configured(AIRBYTE_CONFIG),
        "dbt": dbt_cli_resource.configured(DBT_CONFIG),
        "io_manager": fs_asset_io_manager,
    },
)


@repository
def analytics_repo():
    return [asset_group.build_job("daily_analytics")]
