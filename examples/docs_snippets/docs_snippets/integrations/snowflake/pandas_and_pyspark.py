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
from dagster_snowflake import SnowflakeIOManager
from dagster_snowflake_pandas import SnowflakePandasTypeHandler
from dagster_snowflake_pyspark import SnowflakePySparkTypeHandler

from dagster import Definitions, EnvVar


class SnowflakePandasPySparkIOManager(SnowflakeIOManager):
    @staticmethod
    def type_handlers():
        """type_handlers should return a list of the TypeHandlers that the I/O manager can use.
        Here we return the SnowflakePandasTypeHandler and SnowflakePySparkTypeHandler so that the I/O
        manager can store Pandas DataFrames and PySpark DataFrames.
        """
        return [SnowflakePandasTypeHandler(), SnowflakePySparkTypeHandler()]

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
        "io_manager": SnowflakePandasPySparkIOManager(
            account="abc1234.us-east-1",
            user=EnvVar("SNOWFLAKE_USER"),
            password=EnvVar("SNOWFLAKE_PASSWORD"),
            database="FLOWERS",
            role="writer",
            warehouse="PLANTS",
            schema="IRIS",
        )
    },
)


# end_example
