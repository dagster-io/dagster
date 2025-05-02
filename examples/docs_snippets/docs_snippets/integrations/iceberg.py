import pyarrow as pa
from dagster_iceberg.config import IcebergCatalogConfig
from dagster_iceberg.io_manager.arrow import PyArrowIcebergIOManager

import dagster as dg


@dg.asset
def my_table() -> pa.Table:
    n_legs = pa.array([2, 4, 5, 100])
    animals = pa.array(["Flamingo", "Horse", "Brittle stars", "Centipede"])
    names = ["n_legs", "animals"]
    return pa.Table.from_arrays([n_legs, animals], names=names)


defs = dg.Definitions(
    assets=[my_table],
    resources={
        "io_manager": PyArrowIcebergIOManager(
            name="default",
            config=IcebergCatalogConfig(
                properties={
                    "type": "sql",
                    "uri": "sqlite:////tmp/warehouse/pyiceberg_catalog.db",
                    "warehouse": "file:///tmp/warehouse",
                }
            ),
            namespace="default",
        )
    },
)
