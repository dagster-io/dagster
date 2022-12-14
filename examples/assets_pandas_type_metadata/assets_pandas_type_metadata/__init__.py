from dagster import Definitions, load_assets_from_package_module

from . import assets, lib
from .resources.csv_io_manager import local_csv_io_manager

defs = Definitions(
    assets=load_assets_from_package_module(assets), resources={"io_manager": local_csv_io_manager}
)
