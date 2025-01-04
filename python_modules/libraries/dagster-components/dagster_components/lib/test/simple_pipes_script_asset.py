import shutil
from pathlib import Path
from typing import TYPE_CHECKING

from dagster._core.definitions.asset_key import AssetKey
from dagster._core.definitions.decorators.asset_decorator import asset
from dagster._core.definitions.definitions_class import Definitions
from dagster._core.execution.context.asset_execution_context import AssetExecutionContext
from dagster._core.pipes.subprocess import PipesSubprocessClient
from pydantic import BaseModel, TypeAdapter
from typing_extensions import Self

from dagster_components import Component, ComponentLoadContext, component_type
from dagster_components.core.component_decl_builder import YamlComponentDecl
from dagster_components.core.component_generator import ComponentGenerateRequest, ComponentGenerator
from dagster_components.generate import generate_component_yaml

if TYPE_CHECKING:
    from dagster_components.core.component import ComponentDeclNode


# Same schema used for file generation and defs generation
class SimplePipesScriptAssetParams(BaseModel):
    asset_key: str
    filename: str


class SimplePipesScriptAssetGenerator(ComponentGenerator):
    generator_params = SimplePipesScriptAssetParams

    def generate_files(
        self, request: ComponentGenerateRequest, params: SimplePipesScriptAssetParams
    ) -> None:
        generate_component_yaml(request, params.model_dump())
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

    params_schema = SimplePipesScriptAssetParams

    @classmethod
    def get_generator(cls) -> ComponentGenerator:
        return SimplePipesScriptAssetGenerator()

    @classmethod
    def from_decl_node(
        cls, context: "ComponentLoadContext", decl_node: "ComponentDeclNode"
    ) -> Self:
        assert isinstance(decl_node, YamlComponentDecl)
        loaded_params = TypeAdapter(cls.params_schema).validate_python(
            decl_node.component_file_model.params
        )
        return cls(
            asset_key=AssetKey.from_user_string(loaded_params.asset_key),
            script_path=decl_node.path / loaded_params.filename,
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
