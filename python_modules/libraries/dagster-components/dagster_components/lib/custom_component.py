from abc import abstractmethod
from typing import Any, Optional, Mapping
from typing_extensions import Self
from dagster._core.definitions.definitions_class import Definitions


from dagster_components.core.component import (
    Component,
    ComponentLoadContext,
    component,
    ComponentDeclNode,
    ComponentGenerateRequest,
)


@component(name="custom_component")
class CustomComponent(Component):
    @classmethod
    def generate_files(
        cls, request: ComponentGenerateRequest, params: Any
    ) -> Optional[Mapping[str, Any]]: ...

    @abstractmethod
    def build_defs(self, context: "ComponentLoadContext") -> "Definitions": ...

    @classmethod
    @abstractmethod
    def from_decl_node(
        cls, context: "ComponentLoadContext", decl_node: "ComponentDeclNode"
    ) -> Self: ...
