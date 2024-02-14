import os
import requests
from dagster import asset
from resource import snowflake


@asset
def get_iris_dataset():
    dataset_url = "https://docs.dagster.io/assets/iris.csv"
    iris_dataset = requests.get(f"https://docs.dagster.io/assets/iris.csv")

    with open("iris.csv", "wb") as output_file:
        output_file.write(iris_dataset.content)


# start
from dagster_snowflake import SnowflakeResource

from dagster import (
    AssetExecutionContext,
    StaticPartitionsDefinition,
    asset,
)


@asset(
    partitions_def=StaticPartitionsDefinition(
        ["Iris-setosa", "Iris-virginica", "Iris-versicolor"]
    ),
)
def iris_dataset_partitioned(
    context: AssetExecutionContext, snowflake: SnowflakeResource
):
    partition_species_str = context.partition_key

    query = f"""
        create table if not exists species (
            sepal_length_cm double,
            sepal_width_cm double,
            petal_length_cm double,
            petal_width_cm double,
            species varchar
        );

        delete from species where species in ('{partition_species_str}');

        insert into species
        select
            sepal_length_cm,
            sepal_width_cm,
            petal_length_cm,
            petal_width_cm,
            species
        from 'iris.csv';
    """

    with snowflake.get_connection() as conn:
        conn.cursor.execute(query)


# end
