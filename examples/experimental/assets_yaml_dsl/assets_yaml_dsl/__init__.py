from dagster import Definitions
from dagster._core.external_execution.subprocess import ExtSubprocess

from .domain_specific_dsl.stocks_dsl import get_stocks_dsl_example_defs
from .pure_assets_dsl.assets_dsl import get_asset_dsl_example_defs

defs = Definitions(
    assets=get_asset_dsl_example_defs() + get_stocks_dsl_example_defs(),
    resources={"ext_subprocess": ExtSubprocess()},
)
