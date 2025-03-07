from pathlib import Path

from dagster import Definitions
from dagster._core.pipes.subprocess import PipesSubprocessClient
from dagster_components import build_component_defs

from .domain_specific_dsl.stocks_dsl import get_stocks_dsl_example_defs
from .pure_assets_dsl.assets_dsl import get_asset_dsl_example_defs

defs = Definitions.merge(
    Definitions(
        assets=get_asset_dsl_example_defs() + get_stocks_dsl_example_defs(),
        resources={"pipes_subprocess_client": PipesSubprocessClient()},
    ),
    build_component_defs(Path(__file__).parent / "components"),
)
