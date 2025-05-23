from dagster_duckdb import DuckDBResource

import dagster as dg

monthly_partition = dg.MonthlyPartitionsDefinition(start_date="2018-01-01")


@dg.asset(
    partitions_def=monthly_partition,
    compute_kind="duckdb",
    deps=[dg.AssetKey("stg_orders")],
    automation_condition=dg.AutomationCondition.eager(),
)
def monthly_orders(context: dg.AssetExecutionContext, duckdb: DuckDBResource):
    partition_date_str = context.partition_key
    month_to_fetch = partition_date_str[:-3]
    table_name = "monthly_orders"

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
            from model.jdbt.stg_orders
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


payment_method_partition = dg.StaticPartitionsDefinition(
    ["credit_card", "coupon", "bank_transfer", "gift_card"]
)


@dg.asset(
    deps=[dg.AssetKey("stg_payments")],
    partitions_def=payment_method_partition,
    compute_kind="duckdb",
    automation_condition=dg.AutomationCondition.eager(),
)
def payment_performance(context: dg.AssetExecutionContext, duckdb: DuckDBResource):
    payment_method_str = context.partition_key
    table_name = "payment_performance"

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
            from model.jdbt.stg_payments
            where category = '{payment_method_partition}'
            group by '{payment_method_partition}', product_name;
            """
        )
        preview_query = f"select * from product_performance where payment_method = '{payment_method_partition}';"
        preview_df = conn.execute(preview_query).fetchdf()
        row_count = conn.execute(
            f"""
            SELECT COUNT(*)
            FROM {table_name}
            WHERE payment_method = '{payment_method_partition}';
            """
        ).fetchone()
        count = row_count[0] if row_count else 0

    return dg.MaterializeResult(
        metadata={
            "row_count": dg.MetadataValue.int(count),
            "preview": dg.MetadataValue.md(preview_df.to_markdown(index=False)),
        }
    )


class AdhocRequestConfig(dg.Config):
    start_date: str
    end_date: str


@dg.asset(
    deps=[dg.AssetKey("orders")],
    compute_kind="python",
)
def adhoc_request(
    config: AdhocRequestConfig, duckdb: DuckDBResource
) -> dg.MaterializeResult:
    query = f"""
        select
            order_id,
            customer_id
        from orders
        where date >= '{config.start_date}'
        and date < '{config.end_date}'
    """

    with duckdb.get_connection() as conn:
        preview_df = conn.execute(query).fetchdf()

    return dg.MaterializeResult(
        metadata={"preview": dg.MetadataValue.md(preview_df.to_markdown(index=False))}
    )



@dg.asset_check(asset=monthly_orders)
def adhoc_request_check(duckdb: DuckDBResource) -> dg.AssetCheckResult:
    with duckdb.get_connection() as conn:
        query_result = conn.execute(
            """
            select count(*)
            from orders
            where order_id is null
            """
        ).fetchone()

        count = query_result[0] if query_result else 0
        return dg.AssetCheckResult(
            passed=count == 0, metadata={"order_id is null": count}
        )