import pandas as pd
from dagster_snowflake import SnowflakeResource
from snowflake.connector.pandas_tools import write_pandas

from dagster import Definitions, EnvVar, MaterializeResult, asset

snowflake = SnowflakeResource(
    account=EnvVar("SNOWFLAKE_ACCOUNT"),  # required
    user=EnvVar("SNOWFLAKE_USER"),  # required
    password=EnvVar("SNOWFLAKE_PASSWORD"),  # password or private key required
    warehouse="PLANTS",
    schema="IRIS",
    role="WRITER",
)


@asset
def iris_dataset(snowflake: SnowflakeResource):
    iris_df = pd.read_csv(
        "https://docs.dagster.io/assets/iris.csv",
        names=[
            "sepal_length_cm",
            "species",
        ],
    )

    with snowflake.get_connection() as conn:
        table_name = "iris_dataset"
        database = "flowers"
        schema = "iris"
        success, number_chunks, rows_inserted, output = write_pandas(
            conn,
            iris_df,
            table_name=table_name,
            database=database,
            schema=schema,
            auto_create_table=True,
            overwrite=True,
            quote_identifiers=False,
        )

    return MaterializeResult(
        metadata={"rows_inserted": rows_inserted},
    )


@asset(deps=["iris_dataset"])
def iris_setosa(snowflake: SnowflakeResource) -> None:
    query = """
        create or replace table iris.iris_setosa as (
            SELECT *
            FROM iris.iris_dataset
            WHERE species = 'Iris-setosa'
        );
    """

    with snowflake.get_connection() as conn:
        conn.cursor.execute(query)  # pyright: ignore[reportFunctionMemberAccess]


defs = Definitions(
    assets=[iris_dataset, iris_setosa], resources={"snowflake": snowflake}
)
