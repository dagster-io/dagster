# type: ignore

# Step 1: Define the assets
# start_define_assets
import dagster as dg


@dg.asset
def customers() -> str:
    return "https://raw.githubusercontent.com/dbt-labs/jaffle-shop-classic/refs/heads/main/seeds/raw_customers.csv"


@dg.asset
def orders() -> str:
    return "https://raw.githubusercontent.com/dbt-labs/jaffle-shop-classic/refs/heads/main/seeds/raw_orders.csv"


@dg.asset
def payments() -> str:
    return "https://raw.githubusercontent.com/dbt-labs/jaffle-shop-classic/refs/heads/main/seeds/raw_payments.csv"


# end_define_assets

# Step 2: Define the assets with resources
# start_define_assets_with_resources
from dagster_duckdb import DuckDBResource

import dagster as dg


@dg.asset
# highlight-start
def customers(duckdb: DuckDBResource):
    # highlight-end

    url = "https://raw.githubusercontent.com/dbt-labs/jaffle-shop-classic/refs/heads/main/seeds/raw_customers.csv"
    table_name = "customers"

    # highlight-start
    with duckdb.get_connection() as conn:
        # highlight-end
        conn.execute(
            f"""
            create or replace table {table_name} as (
                select * from read_csv_auto('{url}')
            )
            """
        )


@dg.asset
# highlight-start
def orders(duckdb: DuckDBResource):
    # highlight-end

    url = "https://raw.githubusercontent.com/dbt-labs/jaffle-shop-classic/refs/heads/main/seeds/raw_orders.csv"
    table_name = "orders"

    # highlight-start
    with duckdb.get_connection() as conn:
        # highlight-end
        conn.execute(
            f"""
            create or replace table {table_name} as (
                select * from read_csv_auto('{url}')
            )
            """
        )


@dg.asset
# highlight-start
def payments(duckdb: DuckDBResource):
    # highlight-end

    url = "https://raw.githubusercontent.com/dbt-labs/jaffle-shop-classic/refs/heads/main/seeds/raw_payments.csv"
    table_name = "payments"

    # highlight-start
    with duckdb.get_connection() as conn:
        # highlight-end
        conn.execute(
            f"""
            create or replace table {table_name} as (
                select * from read_csv_auto('{url}')
            )
            """
        )


# end_define_assets_with_resources


# Step 3: Define assets with dependencies
# start_define_assets_with_dependencies
...


@dg.asset(
    # highlight-start
    deps=["customers", "orders", "payments"],
    # highlight-end
)
def orders_by_month(duckdb: DuckDBResource):
    table_name = "orders_by_month"

    with duckdb.get_connection() as conn:
        conn.execute(
            f"""
            create table if not exists {table_name} (
                ...
            );
            """
        )


# end_define_assets_with_dependencies


# Step 4: Define asset_checks
# start_define_asset_checks
...


@dg.asset_check(asset="orders_by_month")
def orders_by_month_check(duckdb: DuckDBResource) -> dg.AssetCheckResult:
    with duckdb.get_connection() as conn:
        row_count = conn.execute(
            "select count(*) from orders_by_month_check"
        ).fetchone()[0]

    if row_count == 0:
        return dg.AssetCheckResult(
            passed=False, metadata={"message": "Orders by month check failed"}
        )

    return dg.AssetCheckResult(
        passed=True, metadata={"message": "Orders by month check passed"}
    )


# end_define_asset_checks
