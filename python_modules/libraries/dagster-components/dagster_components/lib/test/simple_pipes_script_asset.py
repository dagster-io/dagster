import shutil
from pathlib import Path

from dagster._core.definitions.asset_key import AssetKey
from dagster._core.definitions.decorators.asset_decorator import asset
from dagster._core.definitions.definitions_class import Definitions
from dagster._core.execution.context.asset_execution_context import AssetExecutionContext
from dagster._core.pipes.subprocess import PipesSubprocessClient
from pydantic import BaseModel
from typing_extensions import Self

from dagster_components import Component, ComponentLoadContext, component_type
from dagster_components.core.component_scaffolder import (
    ComponentScaffolder,
    ComponentScaffoldRequest,
)
from dagster_components.scaffold import scaffold_component_yaml


# Same schema used for file generation and defs generation
class SimplePipesScriptAssetParams(BaseModel):
    asset_key: str
    filename: str


class SimplePipesScriptAssetScaffolder(ComponentScaffolder):
    @classmethod
    def get_params_schema_type(cls):
        return SimplePipesScriptAssetParams

    def scaffold(
        self, request: ComponentScaffoldRequest, params: SimplePipesScriptAssetParams
    ) -> None:
        scaffold_component_yaml(request, params.model_dump())
        Path(request.component_instance_root_path, params.filename).write_text(
            _SCRIPT_TEMPLATE.format(asset_key=params.asset_key)
        )


_SCRIPT_TEMPLATE = """
from dagster_pipes import open_dagster_pipes

context = open_dagster_pipes()

context.log.info("Materializing asset {asset_key} from pipes")
context.report_asset_materialization(asset_key="{asset_key}")
"""


@component_type(name="simple_pipes_script_asset")
class SimplePipesScriptAsset(Component):
    """A simple asset that runs a Python script with the Pipes subprocess client.

    Because it is a pipes asset, no value is returned.
    """

    @classmethod
    def get_scaffolder(cls) -> ComponentScaffolder:
        return SimplePipesScriptAssetScaffolder()

    @classmethod
    def get_schema(cls):
        return SimplePipesScriptAssetParams

    @classmethod
    def load(cls, context: "ComponentLoadContext") -> Self:
        loaded_params = context.load_params(cls.get_schema())
        return cls(
            asset_key=AssetKey.from_user_string(loaded_params.asset_key),
            script_path=context.path / loaded_params.filename,
        )

    def __init__(self, asset_key: AssetKey, script_path: Path):
        self._asset_key = asset_key
        self._script_path = script_path

    def build_defs(self, context: ComponentLoadContext) -> Definitions:
        @asset(key=self._asset_key)
        def _asset(context: AssetExecutionContext, pipes_client: PipesSubprocessClient):
            cmd = [shutil.which("python"), self._script_path]
            return pipes_client.run(command=cmd, context=context).get_results()

        return Definitions(assets=[_asset])
