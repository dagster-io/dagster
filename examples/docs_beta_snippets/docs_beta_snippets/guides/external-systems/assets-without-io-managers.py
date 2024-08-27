from dagster_duckdb import DuckDBResource

# from snowflake.connector.pandas_tools import write_pandas
import dagster as dg

raw_sales_data = dg.AssetSpec("raw_sales_data")


@dg.asset(deps=[raw_sales_data])
def clean_sales_data(duckdb: DuckDBResource) -> None:
    with duckdb.get_connection() as conn:
        df = conn.execute("SELECT * FROM raw_sales_data").fetch_df()
        clean_df = df.fillna({"amount": 0.0})
        conn.execute("INSERT into clean_sales_data select * from clean_df")


@dg.asset(deps=[clean_sales_data])
def sales_summary(duckdb: DuckDBResource) -> None:
    with duckdb.get_connection() as conn:
        df = conn.execute("SELECT * FROM clean_sales_data").fetch_df()
        summary = df.groupby(["owner"])["amount"].sum().reset_index()
        conn.execute("INSERT into sales_summary select * from summary")


defs = dg.Definitions(
    assets=[raw_sales_data, clean_sales_data, sales_summary],
    resources={"duckdb": DuckDBResource(database="sales.duckdb")},
)
