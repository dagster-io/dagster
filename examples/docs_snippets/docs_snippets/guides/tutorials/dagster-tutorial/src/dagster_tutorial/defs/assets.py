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
def orders_aggregation(duckdb: DuckDBResource):
    table_name = "orders_aggregation"

    with duckdb.get_connection() as conn:
        conn.execute(
            f"""
            create or replace table {table_name} as (
                select
                    c.id as customer_id,
                    c.first_name,
                    c.last_name,
                    count(distinct o.id) as total_orders,
                    count(distinct p.id) as total_payments,
                    coalesce(sum(p.amount), 0) as total_amount_spent
                from customers c
                left join orders o
                    on c.id = o.user_id
                left join payments p
                    on o.id = p.order_id
                group by 1, 2, 3
            );
            """
        )


# end_define_assets_with_dependencies


# Step 4: Define asset_checks
# start_define_asset_checks
...


@dg.asset_check(asset="orders_aggregation")
def orders_aggregation_check(duckdb: DuckDBResource) -> dg.AssetCheckResult:
    table_name = "orders_aggregation"
    with duckdb.get_connection() as conn:
        row_count = conn.execute(f"select count(*) from {table_name}").fetchone()[0]

    if row_count == 0:
        return dg.AssetCheckResult(
            passed=False, metadata={"message": "Order aggregation check failed"}
        )

    return dg.AssetCheckResult(
        passed=True, metadata={"message": "Order aggregation check passed"}
    )


# end_define_asset_checks
