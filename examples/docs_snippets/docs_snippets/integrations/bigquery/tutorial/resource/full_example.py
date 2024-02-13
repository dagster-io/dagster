import pandas as pd
from dagster_gcp import BigQueryResource
from google.cloud import bigquery as bq

from dagster import Definitions, SourceAsset, asset

iris_harvest_data = SourceAsset(key="iris_harvest_data")


@asset
def iris_data(bigquery: BigQueryResource) -> None:
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

    with bigquery.get_client() as client:
        job = client.load_table_from_dataframe(
            dataframe=iris_df,
            destination="iris.iris_data",
        )
        job.result()


@asset(deps=[iris_data])
def iris_setosa(bigquery: BigQueryResource) -> None:
    job_config = bq.QueryJobConfig(destination="iris.iris_setosa")
    sql = "SELECT * FROM iris.iris_data WHERE species = 'Iris-setosa'"

    with bigquery.get_client() as client:
        job = client.query(sql, job_config=job_config)
        job.result()


defs = Definitions(
    assets=[iris_data, iris_setosa, iris_harvest_data],
    resources={
        "bigquery": BigQueryResource(
            project="my-gcp-project",
            location="us-east5",
        )
    },
)
