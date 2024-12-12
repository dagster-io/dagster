import os
from abc import abstractmethod
from pathlib import Path
from typing import TYPE_CHECKING, Any, Mapping, Optional

from dagster._utils import snakecase
from pydantic import BaseModel

from dagster_components.core.component import (
    Component,
    ComponentGenerateRequest,
    ComponentLoadContext,
    component,
)
from dagster_components.generate import generate_component_yaml

if TYPE_CHECKING:
    from dagster._core.definitions.definitions_class import Definitions

CUSTOM_COMPONENT_TEMPLATE = """
from dagster import Definitions
from pydantic import BaseModel, TypeAdapter
from typing_extensions import Self

from dagster_components import ComponentLoadContext, component
from dagster_components.core.component_decl_builder import ComponentDeclNode, YamlComponentDecl
from dagster_components.lib.custom_component import CustomComponent


class {{class_name}}Params(BaseModel): ...


@component(name="{{custom_component_type_name}}")
class {{class_name}}(CustomComponent):
    params_schema = {{class_name}}Params 

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

"""


class GenerateCustomComponentParams(BaseModel):
    class_name: str


@component(name="custom_component")
class CustomComponent(Component):
    @classmethod
    def generate_files(
        cls, request: ComponentGenerateRequest, params: GenerateCustomComponentParams
    ) -> Optional[Mapping[str, Any]]:
        generate_component_yaml(request, {})
        replication_path = Path(os.getcwd()) / "replication.yaml"
        with open(replication_path, "w") as f:
            custom_component_type_name = snakecase(params.class_name)
            f.write(
                CUSTOM_COMPONENT_TEMPLATE.format(
                    class_name=params.class_name,
                    custom_component_type_name=custom_component_type_name,
                )
            )

    @abstractmethod
    def build_defs(self, context: "ComponentLoadContext") -> "Definitions": ...
