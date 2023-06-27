"""This is used to generate the image on code snippet on the dbt front page.

We pull off some dark magic so that generating the screenshot doesn't involve a whole setup with
Fivetran and a database.
"""

from dagster import asset


class dagster_fivetran:
    @staticmethod
    def build_fivetran_assets(connector_id, table_names):
        @asset(compute_kind="fivetran")
        def users():
            ...

        @asset(compute_kind="fivetran")
        def orders():
            ...

        return [users, orders]


class dagster_dbt:
    @staticmethod
    def load_assets_from_dbt_manifest(manifest):
        @asset(non_argument_deps={"users"}, compute_kind="dbt")
        def stg_users():
            """Users with test accounts removed."""
            ...

        @asset(non_argument_deps={"orders"}, compute_kind="dbt")
        def stg_orders():
            """Cleaned orders table."""
            ...

        @asset(non_argument_deps={"stg_users", "stg_orders"}, compute_kind="dbt")
        def daily_order_summary():
            """Summary of daily orders, by user."""
            raise ValueError()

        return [stg_users, stg_orders, daily_order_summary]


# start
fivetran_assets = dagster_fivetran.build_fivetran_assets(
    connector_id="postgres",
    table_names=["users", "orders"],
)

dbt_assets = dagster_dbt.load_assets_from_dbt_manifest("manifest.json")


@asset(compute_kind="tensorflow", non_argument_deps={"daily_order_summary"})
def predicted_orders():
    ...


# end
