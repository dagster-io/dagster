from typing import TYPE_CHECKING

from dagster._core.definitions.asset_key import AssetKey
from dagster._core.definitions.decorators.asset_decorator import asset
from dagster._core.definitions.definitions_class import Definitions
from dagster._core.execution.context.asset_execution_context import AssetExecutionContext
from pydantic import BaseModel, TypeAdapter
from typing_extensions import Self

from dagster_components import Component, ComponentLoadContext, component
from dagster_components.core.component import ComponentGenerateRequest
from dagster_components.core.component_decl_builder import YamlComponentDecl
from dagster_components.generate import generate_component_yaml

if TYPE_CHECKING:
    from dagster_components.core.component import ComponentDeclNode


class SimpleAssetParams(BaseModel):
    asset_key: str
    value: str


@component(name="simple_asset")
class SimpleAsset(Component):
    """A simple asset that returns a constant string value."""

    params_schema = SimpleAssetParams

    @classmethod
    def generate_files(cls, request: ComponentGenerateRequest, params: SimpleAssetParams) -> None:
        generate_component_yaml(request, params.model_dump())

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
            value=loaded_params.value,
        )

    def __init__(self, asset_key: AssetKey, value: str):
        self._asset_key = asset_key
        self._value = value

    def build_defs(self, context: ComponentLoadContext) -> Definitions:
        @asset(key=self._asset_key)
        def dummy(context: AssetExecutionContext):
            return self._value

        return Definitions(assets=[dummy])
