# ruff: noqa: F811

# start_serial_execute
import duckdb
import filelock


def serialize_duckdb_query(duckdb_path: str, sql: str):
    """Execute SQL statement with file lock to guarantee cross-process concurrency."""
    lock_path = f"{duckdb_path}.lock"
    with filelock.FileLock(lock_path):
        conn = duckdb.connect(duckdb_path)
        try:
            return conn.execute(sql)
        finally:
            conn.close()


# end_serial_execute


# start_import_url_to_duckdb
...


def import_url_to_duckdb(url: str, duckdb_path: str, table_name: str):
    create_query = f"""
        create or replace table {table_name} as (
            select * from read_csv_auto('{url}')
        )
    """

    serialize_duckdb_query(duckdb_path, create_query)


# end_import_url_to_duckdb


# start_ingest_assets_1
...


import dagster as dg


@dg.asset(kinds={"duckdb"}, key=["target", "main", "raw_customers"])
def raw_customers() -> None:
    import_url_to_duckdb(
        url="https://raw.githubusercontent.com/dbt-labs/jaffle-shop-classic/refs/heads/main/seeds/raw_customers.csv",
        duckdb_path="/tmp/jaffle_platform.duckdb",
        table_name="jaffle_platform.main.raw_customers",
    )


@dg.asset(kinds={"duckdb"}, key=["target", "main", "raw_orders"])
def raw_orders() -> None:
    import_url_to_duckdb(
        url="https://raw.githubusercontent.com/dbt-labs/jaffle-shop-classic/refs/heads/main/seeds/raw_orders.csv",
        duckdb_path="/tmp/jaffle_platform.duckdb",
        table_name="jaffle_platform.main.raw_orders",
    )


@dg.asset(kinds={"duckdb"}, key=["target", "main", "raw_payments"])
def raw_payments() -> None:
    import_url_to_duckdb(
        url="https://raw.githubusercontent.com/dbt-labs/jaffle-shop-classic/refs/heads/main/seeds/raw_payments.csv",
        duckdb_path="/tmp/jaffle_platform.duckdb",
        table_name="jaffle_platform.main.raw_payments",
    )


# end_ingest_assets_1


# start_import_url_to_duckdb_with_resource
from dagster_duckdb import DuckDBResource


def import_url_to_duckdb(url: str, duckdb: DuckDBResource, table_name: str):
    with duckdb.get_connection() as conn:
        row_count = conn.execute(
            f"""
            create or replace table {table_name} as (
                select * from read_csv_auto('{url}')
            )
            """
        ).fetchone()
        assert row_count is not None
        row_count = row_count[0]


# end_import_url_to_duckdb_with_resource


# start_ingest_assets_2
@dg.asset(
    kinds={"duckdb"},
    key=["target", "main", "raw_customers"],
)
# highlight-start
def raw_customers(duckdb: DuckDBResource) -> None:
    # highlight-end
    import_url_to_duckdb(
        url="https://raw.githubusercontent.com/dbt-labs/jaffle-shop-classic/refs/heads/main/seeds/raw_customers.csv",
        duckdb=duckdb,
        table_name="jaffle_platform.main.raw_customers",
    )


@dg.asset(
    kinds={"duckdb"},
    key=["target", "main", "raw_orders"],
)
# highlight-start
def raw_orders(duckdb: DuckDBResource) -> None:
    # highlight-end
    import_url_to_duckdb(
        url="https://raw.githubusercontent.com/dbt-labs/jaffle-shop-classic/refs/heads/main/seeds/raw_orders.csv",
        duckdb=duckdb,
        table_name="jaffle_platform.main.raw_orders",
    )


@dg.asset(
    kinds={"duckdb"},
    key=["target", "main", "raw_payments"],
)
# highlight-start
def raw_payments(duckdb: DuckDBResource) -> None:
    # highlight-end
    import_url_to_duckdb(
        url="https://raw.githubusercontent.com/dbt-labs/jaffle-shop-classic/refs/heads/main/seeds/raw_payments.csv",
        duckdb=duckdb,
        table_name="jaffle_platform.main.raw_payments",
    )


# end_ingest_assets_2


# start_ingest_assets_3
@dg.asset(
    kinds={"duckdb"},
    key=["target", "main", "raw_customers"],
    # highlight-start
    automation_condition=dg.AutomationCondition.on_cron("0 0 * * 1"),  # every Monday at midnight
    # highlight-end
)
def raw_customers(duckdb: DuckDBResource) -> None:
    import_url_to_duckdb(
        url="https://raw.githubusercontent.com/dbt-labs/jaffle-shop-classic/refs/heads/main/seeds/raw_customers.csv",
        duckdb=duckdb,
        table_name="jaffle_platform.main.raw_customers",
    )


@dg.asset(
    kinds={"duckdb"},
    key=["target", "main", "raw_orders"],
    # highlight-start
    automation_condition=dg.AutomationCondition.on_cron("0 0 * * 1"),  # every Monday at midnight
    # highlight-end
)
def raw_orders(duckdb: DuckDBResource) -> None:
    import_url_to_duckdb(
        url="https://raw.githubusercontent.com/dbt-labs/jaffle-shop-classic/refs/heads/main/seeds/raw_orders.csv",
        duckdb=duckdb,
        table_name="jaffle_platform.main.raw_orders",
    )


@dg.asset(
    kinds={"duckdb"},
    key=["target", "main", "raw_payments"],
    # highlight-start
    automation_condition=dg.AutomationCondition.on_cron("0 0 * * 1"),  # every Monday at midnight
    # highlight-end
)
def raw_payments(duckdb: DuckDBResource) -> None:
    import_url_to_duckdb(
        url="https://raw.githubusercontent.com/dbt-labs/jaffle-shop-classic/refs/heads/main/seeds/raw_payments.csv",
        duckdb=duckdb,
        table_name="jaffle_platform.main.raw_payments",
    )


# end_ingest_assets_3


# start_asset_check
@dg.asset_check(
    asset=raw_customers,
    description="Check if there are any null customer_ids in the joined data",
)
def missing_dimension_check(duckdb: DuckDBResource) -> dg.AssetCheckResult:
    table_name = "jaffle_platform.main.raw_customers"

    with duckdb.get_connection() as conn:
        query_result = conn.execute(
            f"""
            select count(*)
            from {table_name}
            where id is null
            """
        ).fetchone()

        count = query_result[0] if query_result else 0
        return dg.AssetCheckResult(passed=count == 0, metadata={"customer_id is null": count})


# end_asset_check


# start_monthly_partition
monthly_partition = dg.MonthlyPartitionsDefinition(start_date="2018-01-01")


# end_monthly_partition


# start_monthly_sales_performance_asset
@dg.asset(
    deps=["stg_orders"],
    kinds={"duckdb"},
    # highlight-start
    partitions_def=monthly_partition,
    # highlight-end
    automation_condition=dg.AutomationCondition.eager(),
    description="Monthly sales performance",
)
def monthly_orders(context: dg.AssetExecutionContext, duckdb: DuckDBResource):
    # highlight-start
    partition_date_str = context.partition_key
    # highlight-end
    month_to_fetch = partition_date_str[:-3]
    table_name = "jaffle_platform.main.monthly_orders"

    with duckdb.get_connection() as conn:
        conn.execute(
            f"""
            create table if not exists {table_name} (
                partition_date varchar,
                status varchar,
                order_num double
            );

            delete from {table_name} where partition_date = '{month_to_fetch}';

            insert into {table_name}
            select
                '{month_to_fetch}' as partition_date,
                status,
                count(*) as order_num
            from jaffle_platform.main.stg_orders
            where strftime(order_date, '%Y-%m') = '{month_to_fetch}'
            group by '{month_to_fetch}', status;
            """
        )

        preview_query = f"select * from {table_name} where partition_date = '{month_to_fetch}';"
        preview_df = conn.execute(preview_query).fetchdf()
        row_count = conn.execute(
            f"""
            select count(*)
            from {table_name}
            where partition_date = '{month_to_fetch}'
            """
        ).fetchone()
        count = row_count[0] if row_count else 0

    return dg.MaterializeResult(
        metadata={
            "row_count": dg.MetadataValue.int(count),
            "preview": dg.MetadataValue.md(preview_df.to_markdown(index=False)),
        }
    )


# end_monthly_sales_performance_asset


# start_monthly_sales_performance_asset_highlight
@dg.asset(
    deps=["stg_orders"],
    kinds={"duckdb"},
    partitions_def=monthly_partition,
    # highlight-start
    automation_condition=dg.AutomationCondition.eager(),
    # highlight-end
    description="Monthly sales performance",
)
def monthly_orders(context: dg.AssetExecutionContext, duckdb: DuckDBResource):
    # end_monthly_sales_performance_asset_highlight
    partition_date_str = context.partition_key
    month_to_fetch = partition_date_str[:-3]
    table_name = "jaffle_platform.main.monthly_orders"

    with duckdb.get_connection() as conn:
        conn.execute(
            f"""
            create table if not exists {table_name} (
                partition_date varchar,
                status varchar,
                order_num double
            );

            delete from {table_name} where partition_date = '{month_to_fetch}';

            insert into {table_name}
            select
                '{month_to_fetch}' as partition_date,
                status,
                count(*) as order_num
            from jaffle_platform.main.stg_orders
            where strftime(order_date, '%Y-%m') = '{month_to_fetch}'
            group by '{month_to_fetch}', status;
            """
        )

        preview_query = f"select * from {table_name} where partition_date = '{month_to_fetch}';"
        preview_df = conn.execute(preview_query).fetchdf()
        row_count = conn.execute(
            f"""
            select count(*)
            from {table_name}
            where partition_date = '{month_to_fetch}'
            """
        ).fetchone()
        count = row_count[0] if row_count else 0

    return dg.MaterializeResult(
        metadata={
            "row_count": dg.MetadataValue.int(count),
            "preview": dg.MetadataValue.md(preview_df.to_markdown(index=False)),
        }
    )


# start_adhoc_request_asset
class AdhocRequestConfig(dg.Config):
    start_date: str
    end_date: str


@dg.asset(
    deps=["stg_orders"],
    kinds={"python"},
    description="Adhoc order requests",
)
def adhoc_request(config: AdhocRequestConfig, duckdb: DuckDBResource) -> dg.MaterializeResult:
    table_name = "jaffle_platform.main.stg_orders"

    with duckdb.get_connection() as conn:
        preview_df = conn.execute(
            f"""
            select
                order_id,
                customer_id
            from {table_name}
            where date >= '{config.start_date}'
            and date < '{config.end_date}'
            """
        ).fetchdf()

    return dg.MaterializeResult(
        metadata={"preview": dg.MetadataValue.md(preview_df.to_markdown(index=False))}
    )


# end_adhoc_request_asset
