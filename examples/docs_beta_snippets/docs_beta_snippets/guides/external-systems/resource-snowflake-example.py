import pandas as pd
from dagster_snowflake import SnowflakeResource
from snowflake.connector.pandas_tools import write_pandas

import dagster as dg


# An asset that uses a Snowflake resource called iris_db
# and creates a new table from a Pandas dataframe
@dg.asset
def iris_dataset(iris_db: SnowflakeResource) -> None:
    iris_df = pd.read_csv(
        "https://docs.dagster.io/assets/iris.csv",
        names=[
            "sepal_length_cm",
            "sepal_width_cm",
            "petal_length_cm",
            "petal_width_cm",
            "species",
        ],
    )

    with iris_db.get_connection() as conn:
        write_pandas(conn, iris_df, table_name="iris_dataset")


# An asset that uses a Snowflake resource called iris_db
# and creates a new table from an existing table
@dg.asset(deps=[iris_dataset])
def iris_setosa(iris_db: SnowflakeResource) -> None:
    with iris_db.get_connection() as conn:
        conn.cursor().execute("""
            CREATE OR REPALCE TABLE iris_setosa as (
            SELECT *
            FROM iris.iris_dataset
            WHERE species = 'Iris-setosa'
        );""")


defs = dg.Definitions(
    assets=[iris_dataset, iris_setosa],
    resources={
        # highlight-start
        "iris_db": SnowflakeResource(
            # Set the SNOWFLAKE_PASSWORD environment variables before running this code
            password=dg.EnvVar("SNOWFLAKE_PASSWORD"),
            # Update the following strings to match your snowflake database
            warehouse="snowflake_warehouse",
            account="snowflake_account",
            user="snowflake_user",
            database="iris_database",
            schema="iris_schema",
        )
        # highlight-end
    },
)
