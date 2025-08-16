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
import dagster as dg
from dagster_duckdb import DuckDBResource

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
        row_count = conn.execute("select count(*) from orders_by_month_check").fetchone()[0]

    if row_count == 0:
        return dg.AssetCheckResult(
            passed=False,
            metadata={"message": "Orders by month check failed"}
        )

    return dg.AssetCheckResult(
        passed=True,
        metadata={"message": "Orders by month check passed"}
    )

# end_define_asset_checks


# Step 5: Define assets with partitions
...

# start_define_monthly_partition
monthly_partition = dg.MonthlyPartitionsDefinition(start_date="2018-01-01")
# end_define_monthly_partition

# start_define_assets_with_partitions
@dg.asset(
    # highlight-start
    partitions_def=monthly_partition,
    # highlight-end
    deps=["customers", "orders", "payments"],
)
def orders_by_month(context: dg.AssetExecutionContext, duckdb: DuckDBResource):
    partition_date_str = context.partition_key
    month_to_fetch = partition_date_str[:-3]
    table_name = "orders_by_month"

    with duckdb.get_connection() as conn:
        conn.execute(
            f"""
            create table if not exists {table_name} (
                ...
            );

            delete from {table_name} where partition_date = '{month_to_fetch}';

            insert into {table_name} ...;
            """
        )

# end_define_assets_with_partitions


# Step 6: Automation
# start_automation_cron

# highlight-start
@dg.asset(
    automation_condition=dg.AutomationCondition.on_cron("0 0 * * 1"),  
)
# highlight-end
def customers(duckdb: DuckDBResource):
    ...


# highlight-start
@dg.asset(
    automation_condition=dg.AutomationCondition.on_cron("0 0 * * 1"),  
)
# highlight-end
def orders(duckdb: DuckDBResource):
    ...


# highlight-start
@dg.asset(
    automation_condition=dg.AutomationCondition.on_cron("0 0 * * 1"),  
)
# highlight-end
def payments(duckdb: DuckDBResource):
    ...

# end_automation_cron

# start_automation_eager
@dg.asset(
    partitions_def=monthly_partition,
    deps=["customers", "orders", "payments"],
    # highlight-start
    automation_condition=dg.AutomationCondition.eager(),
    # highlight-end
)
def orders_by_month(context: dg.AssetExecutionContext, duckdb: DuckDBResource):
    ...

# end_automation_eager