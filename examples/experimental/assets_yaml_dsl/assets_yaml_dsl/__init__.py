from dagster import Definitions
from dagster._core.external_execution.subprocess import SubprocessExecutionResource

from .assets_dsl import get_asset_dsl_example_defs
from .stocks_dsl import get_stocks_dsl_example_defs

defs = Definitions(
    assets=get_asset_dsl_example_defs() + get_stocks_dsl_example_defs(),
    resources={"subprocess_resource": SubprocessExecutionResource()},
)
