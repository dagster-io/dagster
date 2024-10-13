"""This is used to generate the image on code snippet on the dbt front page.

We pull off some dark magic so that generating the screenshot doesn't involve a whole setup with
Fivetran and a database.
"""

from dagster import asset


class dagster_fivetran:
    @staticmethod
    def build_fivetran_assets(connector_id, table_names):
        @asset(compute_kind="fivetran")
        def users(): ...

        @asset(compute_kind="fivetran")
        def orders(): ...

        return [users, orders]


# start
from pathlib import Path

from dagster_dbt import DbtCliResource, dbt_assets, get_asset_key_for_model
from dagster_fivetran import build_fivetran_assets

from dagster import AssetExecutionContext, asset

fivetran_assets = build_fivetran_assets(
    connector_id="postgres",
    destination_tables=["users", "orders"],
)


@dbt_assets(manifest=Path("manifest.json"))
def dbt_project_assets(context: AssetExecutionContext, dbt: DbtCliResource):
    yield from dbt.cli(["build"], context=context).stream()


@asset(
    compute_kind="tensorflow",
    deps=[get_asset_key_for_model([dbt_project_assets], "daily_order_summary")],
)
def predicted_orders(): ...


# end
