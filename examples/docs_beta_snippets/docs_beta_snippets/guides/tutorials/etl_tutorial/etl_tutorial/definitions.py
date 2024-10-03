import dagster as dg
from dagster_duckdb import DuckDBResource
import json, os

# formatting for metadata
def query_to_markdown(conn, query, limit=10):
    result = conn.execute(query).fetchdf()
    if result.empty:
        return "No results found."
    
    return result.head(limit).to_markdown(index=False)

@dg.asset(
    compute_kind="DuckDB",
    group_name="ingestion"
)
def products(duckdb: DuckDBResource)-> dg.MaterializeResult:
    with duckdb.get_connection() as conn:
        conn.execute("""
                     DROP TABLE IF EXISTS products;
                     CREATE TABLE products AS SELECT * FROM read_csv_auto('data/products.csv')
                     """)

        # asset metadata
        preview_query = "SELECT * FROM products LIMIT 10"
        preview_md = query_to_markdown(conn, preview_query)
        row_count = conn.execute("SELECT COUNT(*) FROM products").fetchone()[0]
        
        return dg.MaterializeResult(
            metadata={
                "row_count": dg.MetadataValue.int(row_count),
                "preview": dg.MetadataValue.md(preview_md),
            }
        )
    

@dg.asset(
    compute_kind="DuckDB",
    group_name="ingestion"
)
def sales_reps(duckdb: DuckDBResource) -> dg.MaterializeResult:
    with duckdb.get_connection() as conn:
        conn.execute("""
                     DROP TABLE IF EXISTS Sales_reps;
                     CREATE TABLE sales_reps AS SELECT * FROM read_csv_auto('data/sales_reps.csv')
                     """)
        
        # asset metadata
        preview_query = "SELECT * FROM sales_reps LIMIT 10"
        preview_md = query_to_markdown(conn, preview_query)
        row_count = conn.execute("SELECT COUNT(*) FROM sales_reps").fetchone()[0]
        
        return dg.MaterializeResult(
            metadata={
                "row_count": dg.MetadataValue.int(row_count),
                "preview": dg.MetadataValue.md(preview_md),
            }
        )
    


@dg.asset(
    compute_kind="DuckDB",
    group_name="ingestion",
)
def sales_data(duckdb: DuckDBResource) -> dg.MaterializeResult:
    with duckdb.get_connection() as conn:
        conn.execute("""
                     DROP TABLE IF EXISTS sales_data;
                     CREATE TABLE sales_data AS SELECT * FROM read_csv_auto('data/sales_data.csv')
                     """)
        # asset metadata
        preview_query = "SELECT * FROM sales_data LIMIT 10"
        preview_md = query_to_markdown(conn, preview_query)
        row_count = conn.execute("SELECT COUNT(*) FROM sales_data").fetchone()[0]
        
        return dg.MaterializeResult(
            metadata={
                "row_count": dg.MetadataValue.int(row_count),
                "preview": dg.MetadataValue.md(preview_md),
            }
        )

# step 1: adding dependencies
@dg.asset(
    compute_kind="DuckDB",
    group_name="joins",
    deps=[sales_data, sales_reps, products]
)
def joined_data(duckdb: DuckDBResource) -> dg.MaterializeResult:
    with duckdb.get_connection() as conn:
        conn.execute("""
                     DROP VIEW IF EXISTS joined_data;
                     CREATE VIEW joined_data AS 
                     SELECT 
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
                     FROM sales_data
                     LEFT JOIN sales_reps
                        on sales_reps.rep_id = sales_data.rep_id
                     LEFT JOIN products
                        on products.product_id = sales_data.product_id
                     """)
        
        
        # asset metadata
        preview_query = "SELECT * FROM joined_data LIMIT 10"
        preview_md = query_to_markdown(conn, preview_query)
        row_count = conn.execute("SELECT COUNT(*) FROM joined_data").fetchone()[0]
        
        return dg.MaterializeResult(
            metadata={
                "row_count": dg.MetadataValue.int(row_count),
                "preview": dg.MetadataValue.md(preview_md),
            }
        )
    
# asset checks
@dg.asset_check(asset=joined_data)
def missing_dimension_check(duckdb: DuckDBResource) -> dg.AssetCheckResult:
    with duckdb.get_connection() as conn:
        query_result = conn.execute("""
                        SELECT count(*) FROM joined_data
                        where rep_name is null
                        or product_name is null
                        """).fetchone()
        result = query_result[0] == 0
        return dg.AssetCheckResult(
            passed=result,
            metadata={"missing dimensions": query_result[0]}
        )
    


# datetime partitions & automaterializations
monthly_partition = dg.MonthlyPartitionsDefinition(start_date="2024-01-01")

@dg.asset(
    deps=[joined_data],
    partitions_def=monthly_partition,
    group_name="analysis",
    compute_kind="DuckDB",
    auto_materialize_policy=dg.AutoMaterializePolicy.eager(),
)
def monthly_sales_performance(context: dg.AssetExecutionContext, duckdb: DuckDBResource):
    partition_date_str = context.partition_key
    month_to_fetch = partition_date_str[:-3]
    
    with duckdb.get_connection() as conn:
        conn.execute(f"""
                CREATE TABLE IF NOT EXISTS monthly_sales_performance (
                    partition_date varchar, 
                    rep_name varchar, 
                    product varchar,
                    total_dollar_amount double
                );

                DELETE FROM monthly_sales_performance WHERE partition_date = '{month_to_fetch}';
            
                INSERT INTO monthly_sales_performance
                SELECT
                    '{month_to_fetch}' as partition_date,
                    rep_name, 
                    product_name,
                    sum(dollar_amount) as total_dollar_amount
                FROM joined_data WHERE strftime(date, '%Y-%m') = '{month_to_fetch}'
                GROUP BY
                '{month_to_fetch}',
                rep_name,
                product_name
                ;
                """
            )
        preview_query = f"SELECT * FROM monthly_sales_performance WHERE partition_date = '{month_to_fetch}';"
        preview_md = query_to_markdown(conn, preview_query)
        row_count = conn.execute(f"SELECT COUNT(*) FROM monthly_sales_performance WHERE partition_date = '{month_to_fetch}';").fetchone()[0]
    
    return dg.MaterializeResult(
        metadata={
            "row_count": dg.MetadataValue.int(row_count),
            "preview": dg.MetadataValue.md(preview_md),
        }
    )

# defined partitions
product_category_partition = dg.StaticPartitionsDefinition(["Electronics", "Books", "Home and Garden", "Clothing"])


@dg.asset(
    deps=[joined_data],
    partitions_def=product_category_partition,
    group_name="analysis",
    compute_kind="DuckDB",
    auto_materialize_policy=dg.AutoMaterializePolicy.eager(),
)
def product_performance(context: dg.AssetExecutionContext, duckdb: DuckDBResource):
    product_category_str = context.partition_key

    with duckdb.get_connection() as conn:
        conn.execute(f"""
                CREATE TABLE IF NOT EXISTS product_performance (
                    product_category varchar, 
                    product_name varchar,
                    total_dollar_amount double,
                    total_units_sold double
                );

                DELETE FROM product_performance WHERE product_category = '{product_category_str}';
            
                INSERT INTO product_performance
                SELECT
                    '{product_category_str}' as product_category,
                    product_name,
                    sum(dollar_amount) as total_dollar_amount,
                    sum(quantity) as total_units_sold
                FROM joined_data 
                WHERE category = '{product_category_str}'
                GROUP BY
                '{product_category_str}',
                product_name
                ;
                """
            )
        preview_query = f"SELECT * FROM product_performance WHERE product_category = '{product_category_str}';"
        preview_md = query_to_markdown(conn, preview_query)
        row_count = conn.execute(f"SELECT COUNT(*) FROM product_performance WHERE product_category = '{product_category_str}';").fetchone()[0]
    
    return dg.MaterializeResult(
        metadata={
            "row_count": dg.MetadataValue.int(row_count),
            "preview": dg.MetadataValue.md(preview_md),
        }
    )

# jobs 
analysis_assets = dg.AssetSelection.keys("joined_data").upstream() 

analysis_update_job = dg.define_asset_job(
    name="analysis_update_job",
    selection=analysis_assets,
)
weekly_update_schedule = dg.ScheduleDefinition(
    job=analysis_update_job,
    cron_schedule="0 0 * * 1", # every Monday at midnight
)


# sensor asset

class AdhocRequestConfig(dg.Config):
    department: str
    product: str
    start_date: str
    end_date: str

@dg.asset(
    deps=["joined_data"],
    compute_kind="Python",
)
def adhoc_request(config: AdhocRequestConfig, duckdb: DuckDBResource) -> dg.MaterializeResult:

    query = f"""
        SELECT
            department,
            rep_name,
            product_name,
            sum(dollar_amount) as total_sales
        FROM joined_data
        WHERE date >= '{config.start_date}'
        AND date < '{config.end_date}'
        AND department = '{config.department}'
        AND product_name = '{config.product}'
        GROUP BY
            department,
            rep_name,
            product_name
    """

    with duckdb.get_connection() as conn:
        preview_md = query_to_markdown(conn, query)

    return dg.MaterializeResult(
        metadata={
            "preview": dg.MetadataValue.md(preview_md)
        }
    )

# sensor job
adhoc_request_job = dg.define_asset_job(
    name="adhoc_request_job",
    selection=dg.AssetSelection.assets("adhoc_request"),
)

@dg.sensor(
    job=adhoc_request_job
)
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
            if filename not in previous_state or previous_state[filename] != last_modified:
                with open(file_path, "r") as f:
                    request_config = json.load(f)

                runs_to_request.append(dg.RunRequest(
                    run_key=f"adhoc_request_{filename}_{last_modified}",
                    run_config={
                        "ops": {
                            "adhoc_request": {
                                "config": {
                                    **request_config
                                }
                            }
                        }
                    }
                ))

    return dg.SensorResult(
        run_requests=runs_to_request,
        cursor=json.dumps(current_state)
    )


all_assets = dg.load_assets_from_current_module()
all_asset_checks = dg.load_asset_checks_from_current_module()

defs = dg.Definitions(
    assets=all_assets,
    asset_checks=all_asset_checks,
    schedules=[weekly_update_schedule],
    jobs=[analysis_update_job,adhoc_request_job],
    sensors=[adhoc_request_sensor],
    resources={
            "duckdb": DuckDBResource(database="data/mydb.duckdb")  
    }
)
