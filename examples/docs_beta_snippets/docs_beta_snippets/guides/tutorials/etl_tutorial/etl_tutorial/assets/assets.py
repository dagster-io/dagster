import dagster as dg
from dagster_duckdb import DuckDBResource
from ..partitions import monthly_partition, product_category_partition

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
    


# partitions & automaterializations

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
    """
        The response to an request made in the `requests` directory.
        See `requests/README.md` for more information.
    """

    # count the number of trips that picked up in a given borough, aggregated by time of day and hour of day
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