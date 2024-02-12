import pandas as pd
from dagster_snowflake import SnowflakeResource

from dagster import Definitions, EnvVar, SourceAsset, asset

iris_harvest_data = SourceAsset(key="iris_harvest_data")


@asset
def iris_dataset(snowflake: SnowflakeResource) -> None:
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

    with snowflake.get_connection() as conn:
        conn.cursor.execute("CREATE TABLE iris.iris_dataset AS SELECT * FROM iris_df")


@asset(deps=[iris_dataset])
def iris_setosa(snowflake: SnowflakeResource) -> None:
    with snowflake.get_connection() as conn:
        conn.cursor.execute(
            "CREATE TABLE iris.iris_setosa AS SELECT * FROM iris.iris_dataset WHERE"
            " species = 'Iris-setosa'"
        )


defs = Definitions(
    assets=[iris_dataset, iris_harvest_data, iris_setosa],
    resources={
        "snowflake": SnowflakeResource(
            account="abc1234.us-east-1",
            user=EnvVar("SNOWFLAKE_USER"),
            password=EnvVar("SNOWFLAKE_PASSWORD"),
            database="FLOWERS",
            role="writer",
            warehouse="PLANTS",
            schema="IRIS",
        )
    },
)
