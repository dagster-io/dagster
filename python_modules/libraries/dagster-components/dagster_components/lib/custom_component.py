from abc import abstractmethod
from typing import TYPE_CHECKING, Any, Mapping, Optional

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

    @abstractmethod
    def build_defs(self, context: "ComponentLoadContext") -> "Definitions": ...
