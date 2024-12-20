from typing import TYPE_CHECKING, Any

from dagster._core.definitions.decorators.asset_decorator import asset
from dagster._core.definitions.definitions_class import Definitions
from dagster._core.execution.context.asset_execution_context import AssetExecutionContext
from typing_extensions import Self

from dagster_components import Component, ComponentLoadContext, component
from dagster_components.core.component import ComponentGenerateRequest
from dagster_components.core.component_decl_builder import YamlComponentDecl
from dagster_components.generate import generate_component_yaml

if TYPE_CHECKING:
    from dagster_components.core.component import ComponentDeclNode


@component(name="all_metadata_empty_asset")
class AllMetadataEmptyAsset(Component):
    @classmethod
    def from_decl_node(
        cls, context: "ComponentLoadContext", decl_node: "ComponentDeclNode"
    ) -> Self:
        assert isinstance(decl_node, YamlComponentDecl)
        return cls()

    @classmethod
    def generate_files(cls, request: ComponentGenerateRequest, params: Any) -> None:
        generate_component_yaml(request, params)

    def build_defs(self, context: ComponentLoadContext) -> Definitions:
        @asset
        def hardcoded_asset(context: AssetExecutionContext):
            return 1

        return Definitions(assets=[hardcoded_asset])
