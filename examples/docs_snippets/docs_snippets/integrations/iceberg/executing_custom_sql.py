import pandas as pd
from dagster_iceberg.config import IcebergCatalogConfig
from dagster_iceberg.resource import IcebergTableResource

from dagster import Definitions, asset

CATALOG_URI = "sqlite:////home/vscode/workspace/.tmp/examples/catalog.db"
CATALOG_WAREHOUSE = "file:///home/vscode/workspace/.tmp/examples/warehouse"


@asset
def small_petals(iceberg: IcebergTableResource) -> pd.DataFrame:
    return iceberg.load().scan().to_pandas()


defs = Definitions(
    assets=[small_petals],
    resources={
        "iceberg": IcebergTableResource(
            name="test",
            config=IcebergCatalogConfig(
                properties={"uri": CATALOG_URI, "warehouse": CATALOG_WAREHOUSE}
            ),
            namespace="dagster",
            table="ingested_data",  # assuming that `ingested_data` Iceberg table exists
        )
    },
)
