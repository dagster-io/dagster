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
from dagster_deltalake import (
    DeltaLakeIOManager,
    DeltaLakePyArrowTypeHandler,
    LocalConfig,
)
from dagster_deltalake_pandas import DeltaLakePandasTypeHandler
from dagster_deltalake_polars import DeltaLakePolarsTypeHandler

from dagster import Definitions


class DeltaLakePandasPySparkPolarsIOManager(DeltaLakeIOManager):
    @staticmethod
    def type_handlers():
        """type_handlers should return a list of the TypeHandlers that the I/O manager can use.
        Here we return the DeltaLakePandasTypeHandler, DeltaLakePyArrowTypeHandler, and DeltaLakePolarsTypeHandler
        so that the I/O manager can store Pandas DataFrames, PyArrow Tables, and Polars DataFrames.
        """
        return [
            DeltaLakePandasTypeHandler(),
            DeltaLakePyArrowTypeHandler(),
            DeltaLakePolarsTypeHandler(),
        ]

    @staticmethod
    def default_load_type() -> Optional[Type]:
        """If an asset is not annotated with an return type, default_load_type will be used to
        determine which TypeHandler to use to store and load the output.
        In this case, unannotated assets will be stored and loaded as Pandas DataFrames.
        """
        return pd.DataFrame


defs = Definitions(
    assets=[iris_dataset, rose_dataset],
    resources={
        "io_manager": DeltaLakePandasPySparkPolarsIOManager(
            root_uri="path/todeltalake",
            storage_options=LocalConfig(),
            schema="iris",
        )
    },
)


# end_example
