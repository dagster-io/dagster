import inspect
import os
import textwrap
from abc import abstractmethod
from pathlib import Path
from typing import TYPE_CHECKING, Any, Mapping, Optional

from dagster._utils import snakecase
from pydantic import BaseModel

from dagster_components.core.component import (
    Component,
    ComponentGenerateRequest,
    ComponentLoadContext,
    component_type,
)
from dagster_components.generate import generate_custom_component_yaml

if TYPE_CHECKING:
    from dagster._core.definitions.definitions_class import Definitions


def custom_component_template():
    from dagster import Definitions
    from pydantic import BaseModel

    from dagster_components import ComponentLoadContext, component_type
    from dagster_components.lib.custom_component import CustomComponent

    class ClassNamePlaceholderComponentSchema(BaseModel): ...

    @component_type(name="component_type_name_placeholder")
    class ClassNamePlaceholderComponent(CustomComponent):
        params_schema = ClassNamePlaceholderComponentSchema

        def build_defs(self, context: ComponentLoadContext) -> Definitions:
            return Definitions()

        @classmethod
        def load(cls, context: ComponentLoadContext) -> "ClassNamePlaceholderComponent":
            loaded_params = context.load_params(cls.params_schema)
            assert loaded_params  # silence linter complaints
            return cls()


CLASSNAME_PLACEHODLER = "ClassNamePlaceholder"
COMPONENT_TYPE_NAME_PLACEHOLDER = "component_type_name_placeholder"


class GenerateCustomComponentParams(BaseModel):
    class_name: str


@component_type(name="custom")
class CustomComponent(Component):
    """Component base class for generating a custom component local to the component instance."""

    generate_params_schema = GenerateCustomComponentParams

    @classmethod
    def generate_files(
        cls, request: ComponentGenerateRequest, params: GenerateCustomComponentParams
    ) -> Optional[Mapping[str, Any]]:
        component_type_name = snakecase(params.class_name)
        generate_custom_component_yaml(
            request.component_instance_root_path, "." + component_type_name, {}
        )
        replication_path = Path(os.getcwd()) / "component.py"
        with open(replication_path, "w") as f:
            f.write(get_custom_component_template(params.class_name, component_type_name))

    @abstractmethod
    def build_defs(self, context: "ComponentLoadContext") -> "Definitions": ...


def get_custom_component_template(class_name: str, component_type_name: str) -> str:
    raw_source = inspect.getsource(custom_component_template)
    without_decl = raw_source.split("\n", 1)[1]
    dedented = textwrap.dedent(without_decl)
    return dedented.replace(CLASSNAME_PLACEHODLER, class_name).replace(
        COMPONENT_TYPE_NAME_PLACEHOLDER, component_type_name
    )
