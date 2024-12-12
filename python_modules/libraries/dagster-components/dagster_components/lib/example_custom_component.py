from dagster import Definitions
from pydantic import BaseModel, TypeAdapter
from typing_extensions import Self

from dagster_components import ComponentLoadContext, component
from dagster_components.core.component_decl_builder import ComponentDeclNode, YamlComponentDecl
from dagster_components.lib.custom_component import CustomComponent


class ExampleCustomComponentParams(BaseModel): ...


@component(name="example_custom_component")
class ExampleCustomComponent(CustomComponent):
    params_schema = ExampleCustomComponentParams

    def build_defs(self, context: ComponentLoadContext) -> Definitions:
        return Definitions()

    @classmethod
    def from_decl_node(
        cls, context: "ComponentLoadContext", decl_node: "ComponentDeclNode"
    ) -> Self:
        assert isinstance(decl_node, YamlComponentDecl)
        loaded_params = TypeAdapter(cls.params_schema).validate_python(
            decl_node.component_file_model.params
        )
        assert loaded_params  # silence linter complaints
        return ExampleCustomComponent()
