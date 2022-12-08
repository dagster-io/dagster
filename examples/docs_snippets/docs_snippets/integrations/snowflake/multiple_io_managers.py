plot_iris_data = None
blob_storage_io_manager = None

# start_example

import pandas as pd
from dagster_aws.s3.io_manager import s3_pickle_io_manager
from dagster_snowflake_pandas import snowflake_pandas_io_manager

from dagster import asset, repository, with_resources


@asset(io_manager_key="warehouse_io_manager")
def iris_dataset() -> pd.DataFrame:
    return pd.read_csv(
        "https://archive.ics.uci.edu/ml/machine-learning-databases/iris/iris.data",
        names=[
            "Sepal length (cm)",
            "Sepal width (cm)",
            "Petal length (cm)",
            "Petal width (cm)",
            "Species",
        ],
    )


@asset(io_manager_key="blob_io_manager")
def iris_plots(iris_dataset):
    return plot_iris_data(iris_dataset)


@repository
def flowers_analysis_repository():
    return with_resources(
        [iris_dataset, iris_plots],
        resource_defs={
            "warehouse_io_manager": snowflake_pandas_io_manager.configured(
                {
                    "database": "FLOWERS",
                    "schema": "IRIS",
                    "account": "abc1234.us-east-1",
                    "user": {"env": "SNOWFLAKE_USER"},
                    "password": {"env": "SNOWFLAKE_PASSWORD"},
                }
            ),
            "blob_io_manager": s3_pickle_io_manager,
        },
    )


# end_example
