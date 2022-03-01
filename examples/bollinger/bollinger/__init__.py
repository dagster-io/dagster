import warnings

from bollinger.resources.csv_io_manager import local_csv_io_manager

from dagster import AssetGroup, ExperimentalWarning, repository

from . import lib

warnings.filterwarnings("ignore", category=ExperimentalWarning)


@repository
def bollinger():
    return [
        AssetGroup.from_package_name(__name__, resource_defs={"io_manager": local_csv_io_manager})
    ]


__all__ = [
    "bollinger",
    "lib",
]
