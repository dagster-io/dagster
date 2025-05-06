from dagster_iceberg.config import IcebergCatalogConfig
from dagster_iceberg.io_manager.arrow import PyArrowIcebergIOManager

io_manager = PyArrowIcebergIOManager(
    name="test",
    config=IcebergCatalogConfig(
        properties={
            "uri": "postgresql+psycopg2://test:test@localhost:5432/test",
            "warehouse": "file:///path/to/warehouse",
        }
    ),
    namespace="dagster",
)
