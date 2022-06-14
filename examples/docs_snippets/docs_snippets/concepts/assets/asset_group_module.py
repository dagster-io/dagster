# isort: skip_file
# pylint: disable=reimported

from dagster import (
    load_assets_from_package_module,
    repository,
    with_resources,
    define_asset_job,
    fs_io_manager,
)

# start_example

cereal_assets = load_assets_from_package_module(
    cereal,
    group_name="cereal_assets",
)

# end_example
