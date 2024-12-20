from dagster_duckdb import DuckDBResource
from etl_tutorial.partitions import monthly_partition, product_category_partition

import dagster as dg


@dg.asset(
    compute_kind="duckdb",
    group_name="ingestion",
)
def products(duckdb: DuckDBResource) -> dg.MaterializeResult:
    with duckdb.get_connection() as conn:
        conn.execute(
            """
            create or replace table products as (
                select * from read_csv_auto('data/products.csv')
            )
            """
        )

        preview_query = "select * from products limit 10"
        preview_df = conn.execute(preview_query).fetchdf()
        row_count = conn.execute("select count(*) from products").fetchone()
        count = row_count[0] if row_count else 0

        return dg.MaterializeResult(
            metadata={
                "row_count": dg.MetadataValue.int(count),
                "preview": dg.MetadataValue.md(preview_df.to_markdown(index=False)),
            }
        )


@dg.asset(
    compute_kind="duckdb",
    group_name="ingestion",
)
def sales_reps(duckdb: DuckDBResource) -> dg.MaterializeResult:
    with duckdb.get_connection() as conn:
        conn.execute(
            """
            create or replace table sales_reps as (
                select * from read_csv_auto('data/sales_reps.csv')
            )
            """
        )

        preview_query = "select * from sales_reps limit 10"
        preview_df = conn.execute(preview_query).fetchdf()
        row_count = conn.execute("select count(*) from sales_reps").fetchone()
        count = row_count[0] if row_count else 0

        return dg.MaterializeResult(
            metadata={
                "row_count": dg.MetadataValue.int(count),
                "preview": dg.MetadataValue.md(preview_df.to_markdown(index=False)),
            }
        )


@dg.asset(
    compute_kind="duckdb",
    group_name="ingestion",
)
def sales_data(duckdb: DuckDBResource) -> dg.MaterializeResult:
    with duckdb.get_connection() as conn:
        conn.execute(
            """
            drop table if exists sales_data;
            create table sales_data as select * from read_csv_auto('data/sales_data.csv')
            """
        )

        preview_query = "SELECT * FROM sales_data LIMIT 10"
        preview_df = conn.execute(preview_query).fetchdf()
        row_count = conn.execute("select count(*) from sales_data").fetchone()
        count = row_count[0] if row_count else 0

        return dg.MaterializeResult(
            metadata={
                "row_count": dg.MetadataValue.int(count),
                "preview": dg.MetadataValue.md(preview_df.to_markdown(index=False)),
            }
        )


@dg.asset(
    compute_kind="duckdb",
    group_name="joins",
    deps=[sales_data, sales_reps, products],
)
def joined_data(duckdb: DuckDBResource) -> dg.MaterializeResult:
    with duckdb.get_connection() as conn:
        conn.execute(
            """
            create or replace view joined_data as (
                select 
                    date,
                    dollar_amount,
                    customer_name,
                    quantity,
                    rep_name,
                    department,
                    hire_date,
                    product_name,
                    category,
                    price
                from sales_data
                left join sales_reps
                    on sales_reps.rep_id = sales_data.rep_id
                left join products
                    on products.product_id = sales_data.product_id
            )
            """
        )

        preview_query = "select * from joined_data limit 10"
        preview_df = conn.execute(preview_query).fetchdf()

        row_count = conn.execute("select count(*) from joined_data").fetchone()
        count = row_count[0] if row_count else 0

        return dg.MaterializeResult(
            metadata={
                "row_count": dg.MetadataValue.int(count),
                "preview": dg.MetadataValue.md(preview_df.to_markdown(index=False)),
            }
        )


@dg.asset_check(asset=joined_data)
def missing_dimension_check(duckdb: DuckDBResource) -> dg.AssetCheckResult:
    with duckdb.get_connection() as conn:
        query_result = conn.execute(
            """
            select count(*) from joined_data
            where rep_name is null
            or product_name is null
            """
        ).fetchone()

        count = query_result[0] if query_result else 0
        return dg.AssetCheckResult(
            passed=count == 0, metadata={"missing dimensions": count}
        )


@dg.asset(
    partitions_def=monthly_partition,
    compute_kind="duckdb",
    group_name="analysis",
    deps=[joined_data],
    automation_condition=dg.AutomationCondition.eager(),
)
def monthly_sales_performance(
    context: dg.AssetExecutionContext, duckdb: DuckDBResource
):
    partition_date_str = context.partition_key
    month_to_fetch = partition_date_str[:-3]

    with duckdb.get_connection() as conn:
        conn.execute(
            f"""
            create table if not exists monthly_sales_performance (
                partition_date varchar,
                rep_name varchar,
                product varchar,
                total_dollar_amount double
            );

            delete from monthly_sales_performance where partition_date = '{month_to_fetch}';

            insert into monthly_sales_performance
            select
                '{month_to_fetch}' as partition_date,
                rep_name, 
                product_name,
                sum(dollar_amount) as total_dollar_amount
            from joined_data where strftime(date, '%Y-%m') = '{month_to_fetch}'
            group by '{month_to_fetch}', rep_name, product_name;
            """
        )

        preview_query = f"select * from monthly_sales_performance where partition_date = '{month_to_fetch}';"
        preview_df = conn.execute(preview_query).fetchdf()
        row_count = conn.execute(
            f"""
            select count(*)
            from monthly_sales_performance
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


@dg.asset(
    deps=[joined_data],
    partitions_def=product_category_partition,
    group_name="analysis",
    compute_kind="duckdb",
    automation_condition=dg.AutomationCondition.eager(),
)
def product_performance(context: dg.AssetExecutionContext, duckdb: DuckDBResource):
    product_category_str = context.partition_key

    with duckdb.get_connection() as conn:
        conn.execute(
            f"""
            create table if not exists product_performance (
                product_category varchar, 
                product_name varchar,
                total_dollar_amount double,
                total_units_sold double
            );

            delete from product_performance where product_category = '{product_category_str}';

            insert into product_performance
            select
                '{product_category_str}' as product_category,
                product_name,
                sum(dollar_amount) as total_dollar_amount,
                sum(quantity) as total_units_sold
            from joined_data 
            where category = '{product_category_str}'
            group by '{product_category_str}', product_name;
            """
        )
        preview_query = f"select * from product_performance where product_category = '{product_category_str}';"
        preview_df = conn.execute(preview_query).fetchdf()
        row_count = conn.execute(
            f"""
            SELECT COUNT(*)
            FROM product_performance
            WHERE product_category = '{product_category_str}';
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
    department: str
    product: str
    start_date: str
    end_date: str


@dg.asset(
    deps=["joined_data"],
    compute_kind="python",
)
def adhoc_request(
    config: AdhocRequestConfig, duckdb: DuckDBResource
) -> dg.MaterializeResult:
    query = f"""
        select
            department,
            rep_name,
            product_name,
            sum(dollar_amount) as total_sales
        from joined_data
        where date >= '{config.start_date}'
        and date < '{config.end_date}'
        and department = '{config.department}'
        and product_name = '{config.product}'
        group by
            department,
            rep_name,
            product_name
    """

    with duckdb.get_connection() as conn:
        preview_df = conn.execute(query).fetchdf()

    return dg.MaterializeResult(
        metadata={"preview": dg.MetadataValue.md(preview_df.to_markdown(index=False))}
    )
