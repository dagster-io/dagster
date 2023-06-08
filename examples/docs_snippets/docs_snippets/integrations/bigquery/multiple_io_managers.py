plot_data = None

# start_example

import pandas as pd
from dagster_aws.s3.io_manager import s3_pickle_io_manager
from dagster_gcp_pandas import BigQueryPandasIOManager

from dagster import Definitions, asset


@asset(io_manager_key="warehouse_io_manager")
def iris_data() -> pd.DataFrame:
    return pd.read_csv(
        "https://docs.dagster.io/assets/iris.csv",
        names=[
            "sepal_length_cm",
            "sepal_width_cm",
            "petal_length_cm",
            "petal_width_cm",
            "species",
        ],
    )


@asset(io_manager_key="blob_io_manager")
def iris_plots(iris_data):
    # plot_data is a function we've defined somewhere else
    # that plots the data in a DataFrame
    return plot_data(iris_data)


defs = Definitions(
    assets=[iris_data, iris_plots],
    resources={
        "warehouse_io_manager": BigQueryPandasIOManager(
            project="my-gcp-project",
            dataset="IRIS",
        ),
        "blob_io_manager": s3_pickle_io_manager,
    },
)

# end_example
