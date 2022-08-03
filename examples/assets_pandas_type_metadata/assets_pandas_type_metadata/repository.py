from assets_pandas_type_metadata import assets
from assets_pandas_type_metadata.resources.csv_io_manager import local_csv_io_manager

from dagster import load_assets_from_package_module, repository, with_resources


@repository
def assets_pandas_type_metadata():
    return [
        *with_resources(
            load_assets_from_package_module(assets), {"io_manager": local_csv_io_manager}
        )
    ]
