import shutil
from pathlib import Path

from dagster._core.definitions.asset_key import AssetKey
from dagster._core.definitions.decorators.asset_decorator import asset
from dagster._core.definitions.definitions_class import Definitions
from dagster._core.execution.context.asset_execution_context import AssetExecutionContext
from dagster._core.pipes.subprocess import PipesSubprocessClient
from dagster_components import Component, ComponentLoadContext
from dagster_components.component_scaffolding import scaffold_component
from dagster_components.scaffold.scaffold import Scaffolder, ScaffoldRequest, scaffold_with
from pydantic import BaseModel


# Same schema used for file generation and defs generation
class SimplePipesScriptScaffoldParams(BaseModel):
    asset_key: str
    filename: str


class SimplePipesScriptScaffolder(Scaffolder):
    @classmethod
    def get_scaffold_params(cls):
        return SimplePipesScriptScaffoldParams

    def scaffold(self, request: ScaffoldRequest, params: SimplePipesScriptScaffoldParams) -> None:
        scaffold_component(request, params.model_dump())
        Path(request.target_path, params.filename).write_text(
            _SCRIPT_TEMPLATE.format(asset_key=params.asset_key)
        )


_SCRIPT_TEMPLATE = """
from dagster_pipes import open_dagster_pipes

context = open_dagster_pipes()

context.log.info("Materializing asset {asset_key} from pipes")
context.report_asset_materialization(asset_key="{asset_key}")
"""


@scaffold_with(SimplePipesScriptScaffolder)
class SimplePipesScriptComponent(Component):
    """A simple asset that runs a Python script with the Pipes subprocess client.

    Because it is a pipes asset, no value is returned.
    """

    @classmethod
    def get_schema(cls):
        return SimplePipesScriptScaffoldParams

    def __init__(self, asset_key: AssetKey, script_path: Path):
        self._asset_key = asset_key
        self._script_path = script_path

    def build_defs(self, context: ComponentLoadContext) -> Definitions:
        @asset(key=self._asset_key)
        def _asset(context: AssetExecutionContext, pipes_client: PipesSubprocessClient):
            cmd = [shutil.which("python"), self._script_path]
            return pipes_client.run(command=cmd, context=context).get_results()

        return Definitions(assets=[_asset])
