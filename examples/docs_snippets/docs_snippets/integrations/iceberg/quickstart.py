# start_storing_a_dagster_asset

import pyarrow as pa

from dagster import asset


@asset
def my_table() -> pa.Table:
    n_legs = pa.array([2, 4, 5, 100])
    animals = pa.array(["Flamingo", "Horse", "Brittle stars", "Centipede"])
    names = ["n_legs", "animals"]
    return pa.Table.from_arrays([n_legs, animals], names=names)


# end_storing_a_dagster_asset


# start_loading_iceberg_tables

import pyarrow as pa

from dagster import asset


@asset
def my_table_with_year(my_table: pa.Table) -> pa.Table:
    year = [2021, 2022, 2019, 2021]
    return my_table.append_column("year", [year])


# end_loading_iceberg_tables


# start_defining_the_io_manager

from dagster_iceberg.config import IcebergCatalogConfig
from dagster_iceberg.io_manager.arrow import PyArrowIcebergIOManager

from dagster import Definitions

warehouse_path = "/tmp/warehouse"

resources = {
    "io_manager": PyArrowIcebergIOManager(
        name="default",
        config=IcebergCatalogConfig(
            properties={
                "type": "sql",
                "uri": f"sqlite:///{warehouse_path}/pyiceberg_catalog.db",
                "warehouse": f"file://{warehouse_path}",
            }
        ),
        namespace="default",
    )
}

defs = Definitions(assets=[my_table, my_table_with_year], resources=resources)

# end_defining_the_io_manager
