from dagster import Definitions, load_assets_from_package_module

from . import (
    assets,
    lib as lib,
)
from .resources.csv_io_manager import LocalCsvIOManager

defs = Definitions(
    assets=load_assets_from_package_module(assets), resources={"io_manager": LocalCsvIOManager()}
)
