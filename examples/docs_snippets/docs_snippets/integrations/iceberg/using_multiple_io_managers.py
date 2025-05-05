import pandas as pd
from dagster_iceberg.config import IcebergCatalogConfig
from dagster_iceberg.io_manager.pandas import PandasIcebergIOManager

from dagster import Definitions, FilesystemIOManager, asset

CATALOG_URI = "sqlite:////home/vscode/workspace/.tmp/examples/catalog.db"
CATALOG_WAREHOUSE = "file:///home/vscode/workspace/.tmp/examples/warehouse"
FS_BASE_DIR = "/home/vscode/workspace/.tmp/examples/images"


resources = {
    "dwh_io_manager": PandasIcebergIOManager(
        name="test",
        config=IcebergCatalogConfig(
            properties={"uri": CATALOG_URI, "warehouse": CATALOG_WAREHOUSE}
        ),
        namespace="dagster",
    ),
    "blob_io_manager": FilesystemIOManager(base_dir=FS_BASE_DIR),
}


@asset(io_manager_key="dwh_io_manager")
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
def iris_plots(iris_dataset: pd.DataFrame):
    # plot_data is a function we've defined somewhere else
    # that plots the data in a DataFrame
    return iris_dataset["sepal_length_cm"].plot.hist()


defs = Definitions(assets=[iris_dataset, iris_plots], resources=resources)
