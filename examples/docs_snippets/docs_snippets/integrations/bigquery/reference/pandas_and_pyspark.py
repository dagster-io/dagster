from dagster import asset


@asset
def iris_data():
    return None


@asset
def rose_data():
    return None


# start_example

from typing import Optional, Sequence, Type

import pandas as pd
from dagster_gcp import BigQueryIOManager
from dagster_gcp_pandas import BigQueryPandasTypeHandler
from dagster_gcp_pyspark import BigQueryPySparkTypeHandler

from dagster import DbTypeHandler, Definitions


class MyBigQueryIOManager(BigQueryIOManager):
    @staticmethod
    def type_handlers() -> Sequence[DbTypeHandler]:
        """type_handlers should return a list of the TypeHandlers that the I/O manager can use.

        Here we return the BigQueryPandasTypeHandler and BigQueryPySparkTypeHandler so that the I/O
        manager can store Pandas DataFrames and PySpark DataFrames.
        """
        return [BigQueryPandasTypeHandler(), BigQueryPySparkTypeHandler()]

    @staticmethod
    def default_load_type() -> Optional[type]:
        """If an asset is not annotated with an return type, default_load_type will be used to
        determine which TypeHandler to use to store and load the output.

        In this case, unannotated assets will be stored and loaded as Pandas DataFrames.
        """
        return pd.DataFrame


defs = Definitions(
    assets=[iris_data, rose_data],
    resources={
        "io_manager": MyBigQueryIOManager(project="my-gcp-project", dataset="FLOWERS")
    },
)


# end_example
