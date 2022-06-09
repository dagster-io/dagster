from typing import Any
from unittest.mock import MagicMock

from pandas import DataFrame

from dagster import IOManager, io_manager


def create_db_connection() -> Any:
    return MagicMock()


def train_recommender_model(df: DataFrame) -> Any:
    del df


def pickle_to_s3(object: Any, key: str) -> None:
    pass


def fetch_products() -> DataFrame:
    return DataFrame({"product": ["knive"], "category": ["kitchenware"]})


@io_manager
def snowflake_io_manager():
    class SnowflakeIOManager(IOManager):
        def handle_output(self, context, obj):
            del context
            del obj

        def load_input(self, context):
            return DataFrame()

    return SnowflakeIOManager()


@io_manager
def s3_io_manager():
    class S3IOManager(IOManager):
        def handle_output(self, context, obj):
            del context
            del obj

        def load_input(self, context):
            return None

    return S3IOManager()
