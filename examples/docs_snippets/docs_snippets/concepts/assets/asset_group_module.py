# pyright: reportMissingImports=false
# ruff: isort: off

from dagster import (
    load_assets_from_package_module,
)

# start_example

from my_package import cereal

cereal_assets = load_assets_from_package_module(
    cereal,
    group_name="cereal_assets",
)

# end_example
