import pandas as pd
import pyarrow as pa
from dagster_iceberg.config import IcebergCatalogConfig
from dagster_iceberg.io_manager.arrow import PyArrowIcebergIOManager

from dagster import Definitions, asset

CATALOG_URI = "sqlite:////home/vscode/workspace/.tmp/examples/select_columns/catalog.db"
CATALOG_WAREHOUSE = (
    "file:///home/vscode/workspace/.tmp/examples/select_columns/warehouse"
)


resources = {
    "io_manager": PyArrowIcebergIOManager(
        name="test",
        config=IcebergCatalogConfig(
            properties={"uri": CATALOG_URI, "warehouse": CATALOG_WAREHOUSE}
        ),
        namespace="dagster",
    )
}


@asset
def iris_dataset() -> pa.Table:
    return pa.Table.from_pandas(
        pd.read_csv(
            "https://docs.dagster.io/assets/iris.csv",
            names=[
                "sepal_length_cm",
                "sepal_width_cm",
                "petal_length_cm",
                "petal_width_cm",
                "species",
            ],
        )
    )


defs = Definitions(assets=[iris_dataset], resources=resources)
