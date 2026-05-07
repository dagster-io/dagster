# pyright: reportMissingImports=false
# ruff: isort: off

import dagster as dg


# start_example

from my_package import cereal

cereal_assets = dg.load_assets_from_package_module(
    cereal,
    group_name="cereal_assets",
)

# end_example
