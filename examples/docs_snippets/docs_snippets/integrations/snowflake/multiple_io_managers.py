plot_data = None

# start_example

import pandas as pd
from dagster_aws.s3.io_manager import s3_pickle_io_manager
from dagster_snowflake_pandas import SnowflakePandasIOManager

from dagster import Definitions, EnvVar, asset


@asset(io_manager_key="warehouse_io_manager")
def iris_dataset() -> pd.DataFrame:
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
def iris_plots(iris_dataset):
    # plot_data is a function we've defined somewhere else
    # that plots the data in a DataFrame
    return plot_data(iris_dataset)


defs = Definitions(
    assets=[iris_dataset, iris_plots],
    resources={
        "warehouse_io_manager": SnowflakePandasIOManager(
            database="FLOWERS",
            schema="IRIS",
            account="abc1234.us-east-1",
            user=EnvVar("SNOWFLAKE_USER"),
            password=EnvVar("SNOWFLAKE_PASSWORD"),
        ),
        "blob_io_manager": s3_pickle_io_manager,
    },
)

# end_example
