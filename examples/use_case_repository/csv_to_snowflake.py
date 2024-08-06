import pandas as pd
from dagster import asset, Definitions, EnvVar, MaterializeResult
from dagster_snowflake import SnowflakeResource
from snowflake.connector.pandas_tools import write_pandas


@asset
def csv_data() -> pd.DataFrame:
    return pd.read_csv("path/to/your/data.csv")


snowflake = SnowflakeResource(
    account=EnvVar("SNOWFLAKE_ACCOUNT"),
    user=EnvVar("SNOWFLAKE_USER"),
    password=EnvVar("SNOWFLAKE_PASSWORD"),
    warehouse="YOUR_WAREHOUSE",
    database="YOUR_DATABASE",
    schema="YOUR_SCHEMA",
)


@asset(deps=["csv_data"])
def load_to_snowflake(csv_data: pd.DataFrame, snowflake: SnowflakeResource) -> MaterializeResult:
    with snowflake.get_connection() as conn:
        table_name = "your_table_name"
        success, number_chunks, rows_inserted, output = write_pandas(
            conn,
            csv_data,
            table_name=table_name,
            auto_create_table=True,
            overwrite=True,
            quote_identifiers=False,
        )
    return MaterializeResult(metadata={"rows_inserted": rows_inserted})


defs = Definitions(assets=[csv_data, load_to_snowflake], resources={"snowflake": snowflake})
