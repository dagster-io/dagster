plot_iris_data = None

# start_full_example

import pandas as pd
from dagster_aws.s3.io_manager import s3_pickle_io_manager
from dagster_snowflake_pandas import snowflake_pandas_io_manager

from dagster import AssetIn, SourceAsset, asset, repository, with_resources

iris_harvest_data = SourceAsset(
    key=["iris", "iris_harvest_data"], io_manager_key="warehouse_io_manager"
)

daffodil_dataset = SourceAsset(
    key=["daffodil", "daffodil_dataset"], io_manager_key="warehouse_io_manager"
)


@asset(key_prefix=["iris"], io_manager_key="warehouse_io_manager")
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


@asset(key_prefix=["iris"], io_manager_key="warehouse_io_manager")
def iris_cleaned(iris_dataset: pd.DataFrame):
    return iris_dataset.dropna().drop_duplicates()


@asset(
    ins={
        "iris_sepal": AssetIn(
            key="iris_dataset",
            metadata={"columns": ["Sepal length (cm)", "Sepal width (cm)"]},
        )
    },
    key_prefix=["iris"],
    io_manager_key="warehouse_io_manager",
)
def sepal_data(iris_sepal: pd.DataFrame) -> pd.DataFrame:
    iris_sepal["Sepal area (cm2)"] = (
        iris_sepal["Sepal length (cm)"] * iris_sepal["Sepal width (cm)"]
    )
    return iris_sepal


@asset(io_manager_key="blob_io_manager", key_prefix=["iris"])
def iris_plots(iris_dataset):
    return plot_iris_data(iris_dataset)


@repository
def flowers_analysis_repository():
    return with_resources(
        [
            iris_dataset,
            iris_harvest_data,
            daffodil_dataset,
            iris_cleaned,
            sepal_data,
            iris_plots,
        ],
        resource_defs={
            "warehouse_io_manager": snowflake_pandas_io_manager.configured(
                {
                    "account": "abc1234.us-east-1",
                    "user": {"env": "SNOWFLAKE_USER"},
                    "password": {"env": "SNOWFLAKE_PASSWORD"},
                    "database": "FLOWERS",
                }
            ),
            "blob_io_manager": s3_pickle_io_manager,
        },
    )


# end_full_example
