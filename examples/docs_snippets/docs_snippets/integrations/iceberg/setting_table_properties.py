import pandas as pd
from dagster_iceberg.config import IcebergCatalogConfig
from dagster_iceberg.io_manager.pandas import PandasIcebergIOManager

from dagster import Definitions, asset

CATALOG_URI = "sqlite:////home/vscode/workspace/.tmp/examples/select_columns/catalog.db"
CATALOG_WAREHOUSE = (
    "file:///home/vscode/workspace/.tmp/examples/select_columns/warehouse"
)

resources = {
    "io_manager": PandasIcebergIOManager(
        name="test",
        config=IcebergCatalogConfig(
            properties={"uri": CATALOG_URI, "warehouse": CATALOG_WAREHOUSE}
        ),
        namespace="dagster",
    )
}


@asset
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


@asset(
    metadata={
        "table_properties": {
            "write.parquet.page-size-bytes": "2097152",  # 2MB
            "write.parquet.page-row-limit": "10000",
        }
    }
)
def sepal_data(iris_sepal: pd.DataFrame) -> pd.DataFrame:
    iris_sepal["sepal_area_cm2"] = (
        iris_sepal["sepal_length_cm"] * iris_sepal["sepal_width_cm"]
    )
    return iris_sepal


defs = Definitions(assets=[iris_dataset, sepal_data], resources=resources)
