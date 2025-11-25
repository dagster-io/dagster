import daft as da
import pandas as pd
from dagster_iceberg.config import IcebergCatalogConfig
from dagster_iceberg.io_manager.daft import DaftIcebergIOManager

from dagster import Definitions, asset

# Replace with your actual catalog and warehouse paths, or use environment variables to set these values at runtime.
CATALOG_URI = "sqlite:////path/to/your/catalog.db"
CATALOG_WAREHOUSE = "file:///path/to/your/warehouse"


resources = {
    "io_manager": DaftIcebergIOManager(
        name="test",
        config=IcebergCatalogConfig(
            properties={"uri": CATALOG_URI, "warehouse": CATALOG_WAREHOUSE}
        ),
        namespace="dagster",
    )
}


@asset
def iris_dataset() -> da.DataFrame:
    return da.from_pandas(
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
