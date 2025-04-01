import pandas as pd
from dagster_snowflake import SnowflakeResource
from snowflake.connector.pandas_tools import write_pandas

import dagster as dg

iris_db = SnowflakeResource(
    password="snowflake_password",
    warehouse="snowflake_warehouse",
    account="snowflake_account",
    user="snowflake_user",
    database="iris_database",
    schema="iris_schema",
)


@dg.asset
# highlight-start
# Provide the resource to the asset
def iris_dataset(iris_db: SnowflakeResource) -> None:
    # highlight-end
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


# A second asset that uses the `iris_db` resource
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


defs = dg.Definitions(
    assets=[iris_dataset, iris_setosa],
    # highlight-start
    # Include the resource in the `Definitions` object
    resources={"iris_db": iris_db},
    # highlight-end
)
