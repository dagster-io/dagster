from bollinger.resources.csv_io_manager import local_csv_io_manager

from dagster import load_assets_from_package_name, repository, with_resources

from . import lib


@repository
def bollinger():
    return [
        *with_resources(
            load_assets_from_package_name(__name__), {"io_manager": local_csv_io_manager}
        )
    ]


__all__ = [
    "bollinger",
    "lib",
]
