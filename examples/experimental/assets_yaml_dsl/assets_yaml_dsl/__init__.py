from dagster import Definitions

from .assets_dsl import get_asset_dsl_example_defs
from .stocks_dsl import get_stocks_dsl_example_defs
from dagster._core.external_execution.resource import SubprocessExecutionResource

defs = Definitions(
    assets=get_asset_dsl_example_defs() + get_stocks_dsl_example_defs(),
    resources={"subprocess_resource": SubprocessExecutionResource},
)
