from dagster_snowflake import SnowflakeResource
from snowflake.connector.pandas_tools import write_pandas

import dagster as dg

raw_sales_data = dg.AssetSpec("raw_sales_data")


@dg.asset(deps=[raw_sales_data])
def clean_sales_data(snowflake: SnowflakeResource) -> None:
    with snowflake.get_connection() as conn:
        df = conn.cursor.execute("SELECT * FROM raw_sales_data").fetch_pandas_all()
        clean_df = df.fillna({"amount": 0.0})
        write_pandas(conn, clean_df, "clean_sales_data")


@dg.asset(deps=[clean_sales_data])
def sales_summary(snowflake: SnowflakeResource) -> None:
    with snowflake.get_connection() as conn:
        df = conn.cursor.execute("SELECT * FROM clean_sales_data").fetch_pandas_all()
        summary = df.groupby(["owner"])["amount"].sum().reset_index()
        write_pandas(conn, summary, "sales_summary")


defs = dg.Definitions(
    assets=[raw_sales_data, clean_sales_data, sales_summary],
    resources={
        "snowflake": SnowflakeResource(
            account=dg.EnvVar("SNOWFLAKE_ACCOUNT"),
            user=dg.EnvVar("SNOWFLAKE_USER"),
            password=dg.EnvVar("SNOWFLAKE_PASSWORD"),
            database=dg.EnvVar("SNOWFLAKE_DATABASE"),
        )
    },
)
