import json
import os

from dagster_duckdb import DuckDBResource

import dagster as dg


def query_to_markdown(conn, query, limit=10):
    """Performs SQL query and converts result to markdown.

    Args:
        conn(DuckDBPyConnection) connection to duckdb
        query (str): query to run against duckdb connection
        limit (int): maximum number of rows to render to markdown

    Returns:
        Markdown representation of query result

    """
    result = conn.execute(query).fetchdf()
    if result.empty:
        return "No results found."

    return result.head(limit).to_markdown(index=False)


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
        preview_md = query_to_markdown(conn, preview_query)
        row_count = conn.execute("select count(*) from products").fetchone()
        count = row_count[0] if row_count else 0

        return dg.MaterializeResult(
            metadata={
                "row_count": dg.MetadataValue.int(count),
                "preview": dg.MetadataValue.md(preview_md),
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
        preview_md = query_to_markdown(conn, preview_query)
        row_count = conn.execute("select count(*) from sales_reps").fetchone()
        count = row_count[0] if row_count else 0

        return dg.MaterializeResult(
            metadata={
                "row_count": dg.MetadataValue.int(count),
                "preview": dg.MetadataValue.md(preview_md),
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
        preview_md = query_to_markdown(conn, preview_query)
        row_count = conn.execute("select count(*) from sales_data").fetchone()
        count = row_count[0] if row_count else 0

        return dg.MaterializeResult(
            metadata={
                "row_count": dg.MetadataValue.int(count),
                "preview": dg.MetadataValue.md(preview_md),
            }
        )


# step 1: adding dependencies
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
        preview_md = query_to_markdown(conn, preview_query)
        row_count = conn.execute("select count(*) from joined_data").fetchone()
        count = row_count[0] if row_count else 0

        return dg.MaterializeResult(
            metadata={
                "row_count": dg.MetadataValue.int(count),
                "preview": dg.MetadataValue.md(preview_md),
            }
        )


# asset checks
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
            passed=count > 0, metadata={"missing dimensions": count}
        )


# datetime partitions & automaterializations
monthly_partition = dg.MonthlyPartitionsDefinition(start_date="2024-01-01")


@dg.asset(
    partitions_def=monthly_partition,
    compute_kind="duckdb",
    group_name="analysis",
    deps=[joined_data],
    auto_materialize_policy=dg.AutoMaterializePolicy.eager(),
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
        preview_md = query_to_markdown(conn, preview_query)
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
            "preview": dg.MetadataValue.md(preview_md),
        }
    )


# defined partitions
product_category_partition = dg.StaticPartitionsDefinition(
    ["Electronics", "Books", "Home and Garden", "Clothing"]
)


@dg.asset(
    deps=[joined_data],
    partitions_def=product_category_partition,
    group_name="analysis",
    compute_kind="duckdb",
    auto_materialize_policy=dg.AutoMaterializePolicy.eager(),
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
        preview_md = query_to_markdown(conn, preview_query)
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
            "preview": dg.MetadataValue.md(preview_md),
        }
    )


analysis_assets = dg.AssetSelection.keys("joined_data").upstream()

analysis_update_job = dg.define_asset_job(
    name="analysis_update_job",
    selection=analysis_assets,
)

weekly_update_schedule = dg.ScheduleDefinition(
    job=analysis_update_job,
    cron_schedule="0 0 * * 1",  # every Monday at midnight
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
        preview_md = query_to_markdown(conn, query)

    return dg.MaterializeResult(metadata={"preview": dg.MetadataValue.md(preview_md)})


adhoc_request_job = dg.define_asset_job(
    name="adhoc_request_job",
    selection=dg.AssetSelection.assets("adhoc_request"),
)


@dg.sensor(job=adhoc_request_job)
def adhoc_request_sensor(context: dg.SensorEvaluationContext):
    PATH_TO_REQUESTS = os.path.join(os.path.dirname(__file__), "../", "data/requests")

    previous_state = json.loads(context.cursor) if context.cursor else {}
    current_state = {}
    runs_to_request = []

    for filename in os.listdir(PATH_TO_REQUESTS):
        file_path = os.path.join(PATH_TO_REQUESTS, filename)
        if filename.endswith(".json") and os.path.isfile(file_path):
            last_modified = os.path.getmtime(file_path)

            current_state[filename] = last_modified

            # if the file is new or has been modified since the last run, add it to the request queue
            if (
                filename not in previous_state
                or previous_state[filename] != last_modified
            ):
                with open(file_path, "r") as f:
                    request_config = json.load(f)

                runs_to_request.append(
                    dg.RunRequest(
                        run_key=f"adhoc_request_{filename}_{last_modified}",
                        run_config={
                            "ops": {"adhoc_request": {"config": {**request_config}}}
                        },
                    )
                )

    return dg.SensorResult(
        run_requests=runs_to_request, cursor=json.dumps(current_state)
    )


defs = dg.Definitions(
    assets=[
        products,
        sales_reps,
        sales_data,
        joined_data,
        monthly_sales_performance,
        product_performance,
    ],
    asset_checks=[missing_dimension_check],
    schedules=[weekly_update_schedule],
    jobs=[analysis_update_job, adhoc_request_job],
    sensors=[adhoc_request_sensor],
    resources={"duckdb": DuckDBResource(database="data/mydb.duckdb")},
)
