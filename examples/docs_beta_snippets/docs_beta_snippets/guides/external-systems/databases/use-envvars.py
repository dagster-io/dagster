import os

import pandas as pd
from dagster_snowflake import SnowflakeResource
from snowflake.connector.pandas_tools import write_pandas

import dagster as dg

# highlight-start
# Define `local` and `production` versions of the Snowflake resource
resources = {
    "local": {
        "iris_db": SnowflakeResource(
            # Retrieve dev credentials with environment variables
            user=dg.EnvVar("DEV_SNOWFLAKE_USER"),
            password=dg.EnvVar("DEV_SNOWFLAKE_PASSWORD"),
            warehouse="snowflake_warehouse",
            account="abc1234.us-east-1",
            database="LOCAL",
            schema="IRIS_SCHEMA",
        ),
    },
    "production": {
        "iris_db": SnowflakeResource(
            # Retrieve production credentials with environment variables
            user=dg.EnvVar("PROD_SNOWFLAKE_USER"),
            password=dg.EnvVar("PROD_SNOWFLAKE_PASSWORD"),
            warehouse="snowflake_warehouse",
            account="abc1234.us-east-1",
            database="PRODUCTION",
            schema="IRIS_SCHEMA",
        ),
    },
}
# highlight-end


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


@dg.asset(deps=[iris_dataset])
def iris_setosa(iris_db: SnowflakeResource) -> None:
    with iris_db.get_connection() as conn:
        conn.cursor().execute(
            """
            CREATE OR REPALCE TABLE iris_setosa as (
            SELECT *
            FROM iris.iris_dataset
            WHERE species = 'Iris-setosa'
        );"""
        )


# highlight-start
# Define a variable that determines environment; defaults to `local`
deployment_name = os.getenv("DAGSTER_DEPLOYMENT", "local")
# highlight-end

defs = dg.Definitions(
    assets=[iris_dataset, iris_setosa],
    # highlight-start
    # Provide the dictionary of resources to `Definitions`
    resources=resources[deployment_name],
    # highlight-end
)
