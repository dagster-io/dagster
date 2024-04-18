from dagster import Definitions
from dagster._core.pipes.subprocess import PipesSubprocessClient
from examples.experimental.assets_yaml_dsl.assets_yaml_dsl.asset_graph_execution_node import (
    AssetGraphExecutionNode,
)

from .domain_specific_dsl.stocks_dsl import get_stocks_dsl_example_defs
from .pure_assets_dsl.assets_dsl import get_asset_dsl_example_defs

defs = Definitions(
    assets=AssetGraphExecutionNode.to_assets_defs(
        list(get_asset_dsl_example_defs()) + list(get_stocks_dsl_example_defs())
    ),
    resources={"pipes_subprocess_client": PipesSubprocessClient()},
)
