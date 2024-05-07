from dagster import Definitions
from dagster._core.pipes.subprocess import PipesSubprocessClient

from .domain_specific_dsl.stocks_dsl import get_stocks_dsl_example_defs
from .pure_assets_dsl.assets_dsl import get_asset_dsl_targets

defs = Definitions(
    assets=get_stocks_dsl_example_defs(),
    resources={"pipes_subprocess_client": PipesSubprocessClient()},
    targets=get_asset_dsl_targets(),
)
