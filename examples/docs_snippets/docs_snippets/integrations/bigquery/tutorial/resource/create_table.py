# start_example
import pandas as pd
from dagster_gcp import BigQueryResource

from dagster import asset


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


# end_example
