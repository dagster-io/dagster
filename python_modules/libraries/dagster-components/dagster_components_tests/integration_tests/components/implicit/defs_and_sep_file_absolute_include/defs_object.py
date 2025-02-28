from dagster import Definitions
from dagster_components_tests.integration_tests.components.implicit.defs_and_sep_file_absolute_include.side_asset import (
    side_asset,
)

defs = Definitions(
    assets=[side_asset],
)
