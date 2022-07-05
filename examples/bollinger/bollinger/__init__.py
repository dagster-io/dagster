from bollinger.resources.csv_io_manager import local_csv_io_manager

# from bollinger.resources.snowflake_io_manager import snowflake_io_manager
from dagster_snowflake import build_snowflake_io_manager
from dagster_snowflake_pandas import SnowflakePandasTypeHandler

from dagster import load_assets_from_package_name, repository, with_resources

from . import lib

snowflake_io_manager = build_snowflake_io_manager([SnowflakePandasTypeHandler()])


@repository
def bollinger():
    return [
        *with_resources(
            load_assets_from_package_name(__name__),
            {"io_manager": local_csv_io_manager, "snowflake": snowflake_io_manager},
        )
    ]


__all__ = [
    "bollinger",
    "lib",
]
