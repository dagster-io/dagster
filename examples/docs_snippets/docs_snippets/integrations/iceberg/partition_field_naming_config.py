from dagster import Definitions
from dagster_iceberg.config import IcebergCatalogConfig
from dagster_iceberg.io_manager.pandas import PandasIcebergIOManager

CATALOG_URI = "sqlite:////home/vscode/workspace/.tmp/examples/catalog.db"
CATALOG_WAREHOUSE = "file:///home/vscode/workspace/.tmp/examples/warehouse"

resources = {
    "io_manager": PandasIcebergIOManager(
        name="test",
        config=IcebergCatalogConfig(
            properties={"uri": CATALOG_URI, "warehouse": CATALOG_WAREHOUSE},
            partition_field_name_prefix="custom-prefix"
        ),
        namespace="dagster",
    )
}
defs = Definitions(resources=resources, assets=[...])