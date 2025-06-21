from dagster_duckdb import DuckDBResource

import dagster as dg


# start_joined_data_asset
@dg.asset(
    deps=["stg_orders", "stg_customers"],
    kinds={"duckdb"},
    automation_condition=dg.AutomationCondition.on_cron(
        "0 0 * * 1"
    ),  # every Monday at midnight
    description="Joined data between orders and customers",
)
def joined_data(duckdb: DuckDBResource) -> dg.MaterializeResult:
    table_name = "jaffle_platform.main.joined_data"

    with duckdb.get_connection() as conn:
        conn.execute(
            f"""
            create or replace table {table_name} as (
                select 
                    orders.customer_id,
                    orders.status as order_type,
                    count(*) as num_orders
                from jaffle_platform.main.stg_orders as orders
                left join jaffle_platform.main.stg_customers as customers
                    using(customer_id)
                group by 1, 2
            )
            """
        )

        preview_query = f"select * from {table_name} limit 10"
        preview_df = conn.execute(preview_query).fetchdf()

        row_count = conn.execute(f"select count(*) from {table_name}").fetchone()
        count = row_count[0] if row_count else 0

        return dg.MaterializeResult(
            metadata={
                "row_count": dg.MetadataValue.int(count),
                "preview": dg.MetadataValue.md(preview_df.to_markdown(index=False)),
            }
        )


# end_joined_data_asset


# start_asset_check
@dg.asset_check(
    asset=joined_data,
    description="Check if there are any null customer_ids in the joined data",
)
def missing_dimension_check(duckdb: DuckDBResource) -> dg.AssetCheckResult:
    table_name = "jaffle_platform.main.joined_data"

    with duckdb.get_connection() as conn:
        query_result = conn.execute(
            f"""
            select count(*)
            from {table_name}
            where customer_id is null
            """
        ).fetchone()

        count = query_result[0] if query_result else 0
        return dg.AssetCheckResult(
            passed=count == 0, metadata={"customer_id is null": count}
        )


# end_asset_check


# start_monthly_partition
monthly_partition = dg.MonthlyPartitionsDefinition(start_date="2018-01-01")


# end_monthly_partition


# start_monthly_sales_performance_asset
@dg.asset(
    deps=["stg_orders"],
    kinds={"duckdb"},
    partitions_def=monthly_partition,
    automation_condition=dg.AutomationCondition.eager(),
    description="Monthly sales performance",
)
def monthly_orders(context: dg.AssetExecutionContext, duckdb: DuckDBResource):
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

        preview_query = (
            f"select * from {table_name} where partition_date = '{month_to_fetch}';"
        )
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


# start_product_category_partition
payment_method_partition = dg.StaticPartitionsDefinition(
    ["credit_card", "coupon", "bank_transfer", "gift_card"]
)


# end_product_category_partition


# start_product_performance_asset
@dg.asset(
    deps=[dg.AssetKey("stg_payments")],
    kinds={"duckdb"},
    partitions_def=payment_method_partition,
    automation_condition=dg.AutomationCondition.eager(),
    description="Payment performance",
)
def payment_performance(context: dg.AssetExecutionContext, duckdb: DuckDBResource):
    table_name = "jaffle_platform.main.payment_performance"

    with duckdb.get_connection() as conn:
        conn.execute(
            f"""
            create table if not exists {table_name} (
                payment_method varchar, 
                order_num int,
                total_amount int
            );

            delete from {table_name} where payment_method = '{payment_method_partition}';

            insert into {table_name}
            select
                '{payment_method_partition}' as payment_method,
                count(*) as order_num,
                sum(amount) as total_amount
            from jaffle_platform.main.stg_payments
            where category = '{payment_method_partition}'
            group by '{payment_method_partition}', product_name;
            """
        )
        preview_query = f"select * from product_performance where payment_method = '{payment_method_partition}';"
        preview_df = conn.execute(preview_query).fetchdf()
        row_count = conn.execute(
            f"""
            select count(*)
            from {table_name}
            where payment_method = '{payment_method_partition}';
            """
        ).fetchone()
        count = row_count[0] if row_count else 0

    return dg.MaterializeResult(
        metadata={
            "row_count": dg.MetadataValue.int(count),
            "preview": dg.MetadataValue.md(preview_df.to_markdown(index=False)),
        }
    )


# end_product_performance_asset


# start_adhoc_request_asset
class AdhocRequestConfig(dg.Config):
    start_date: str
    end_date: str


@dg.asset(
    deps=["stg_orders"],
    kinds={"python"},
    description="Adhoc order requests",
)
def adhoc_request(
    config: AdhocRequestConfig, duckdb: DuckDBResource
) -> dg.MaterializeResult:
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
