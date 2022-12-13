from assets_pandas_type_metadata import assets
from assets_pandas_type_metadata.resources.csv_io_manager import local_csv_io_manager

from dagster import Definitions, load_assets_from_package_module

defs = Definitions(
    assets=load_assets_from_package_module(assets), resources={"io_manager": local_csv_io_manager}
)
