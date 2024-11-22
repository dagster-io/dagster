from dagster import asset


@asset
def iris_dataset():
    return None


@asset
def rose_dataset():
    return None


# start_example

from typing import Optional, Type

import pandas as pd
from dagster_duckdb import DuckDBIOManager
from dagster_duckdb_pandas import DuckDBPandasTypeHandler
from dagster_duckdb_polars import DuckDBPolarsTypeHandler
from dagster_duckdb_pyspark import DuckDBPySparkTypeHandler

from dagster import Definitions


class DuckDBPandasPySparkPolarsIOManager(DuckDBIOManager):
    @staticmethod
    def type_handlers():
        """type_handlers should return a list of the TypeHandlers that the I/O manager can use.
        Here we return the DuckDBPandasTypeHandler, DuckDBPySparkTypeHandler, and DuckDBPolarsTypeHandler so that the I/O
        manager can store Pandas DataFrames, PySpark DataFrames, and Polars DataFrames.
        """
        return [
            DuckDBPandasTypeHandler(),
            DuckDBPySparkTypeHandler(),
            DuckDBPolarsTypeHandler(),
        ]

    @staticmethod
    def default_load_type() -> Optional[type]:
        """If an asset is not annotated with an return type, default_load_type will be used to
        determine which TypeHandler to use to store and load the output.
        In this case, unannotated assets will be stored and loaded as Pandas DataFrames.
        """
        return pd.DataFrame


defs = Definitions(
    assets=[iris_dataset, rose_dataset],
    resources={
        "io_manager": DuckDBPandasPySparkPolarsIOManager(
            database="path/to/my_duckdb_database.duckdb",
            schema="IRIS",
        )
    },
)


# end_example
