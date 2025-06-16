import pandas as pd
from dagster_iceberg.config import IcebergCatalogConfig
from dagster_iceberg.io_manager.pandas import PandasIcebergIOManager

from dagster import (
    DailyPartitionsDefinition,
    Definitions,
    MultiPartitionsDefinition,
    StaticPartitionsDefinition,
    asset,
)

CATALOG_URI = "sqlite:////home/vscode/workspace/.tmp/examples/catalog.db"
CATALOG_WAREHOUSE = "file:///home/vscode/workspace/.tmp/examples/warehouse"

resources = {
    "io_manager": PandasIcebergIOManager(
        name="test",
        config=IcebergCatalogConfig(
            properties={"uri": CATALOG_URI, "warehouse": CATALOG_WAREHOUSE}
        ),
        namespace="dagster",
    )
}


# start_defining_the_asset


@asset(
    partitions_def=MultiPartitionsDefinition(
        {
            "date": DailyPartitionsDefinition(start_date="2023-01-01"),
            "species": StaticPartitionsDefinition(
                ["Iris-setosa", "Iris-virginica", "Iris-versicolor"]
            ),
        }
    ),
    metadata={
        "partition_expr": {"date": "time", "species": "species"},
        "partition_spec_update_mode": "update",
        "schema_update_mode": "update",
    },
)
def iris_dataset_partitioned(context) -> pd.DataFrame: ...


# end_defining_the_asset


defs = Definitions(assets=[iris_dataset_partitioned], resources=resources)
