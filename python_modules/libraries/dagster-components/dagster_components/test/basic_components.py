"""Sample local components for testing validation. Paired with test cases
in integration_tests/components/validation.
"""

from dagster._core.definitions.definitions_class import Definitions
from pydantic import BaseModel, ConfigDict

from dagster_components import Component, ComponentSchema, registered_component_type
from dagster_components.core.component import ComponentLoadContext


class MyComponentSchema(ComponentSchema):
    a_string: str
    an_int: int

    model_config = ConfigDict(extra="forbid")


@registered_component_type
class MyComponent(Component):
    name = "my_component"

    def __init__(self, a_string: str, an_int: int):
        self.a_string = a_string
        self.an_int = an_int

    @classmethod
    def get_schema(cls) -> type[MyComponentSchema]:
        return MyComponentSchema

    def build_defs(self, context: ComponentLoadContext) -> Definitions:
        return Definitions()


class MyNestedModel(BaseModel):
    a_string: str
    an_int: int

    model_config = ConfigDict(extra="forbid")


class MyNestedComponentSchema(BaseModel):
    nested: dict[str, MyNestedModel]

    model_config = ConfigDict(extra="forbid")


@registered_component_type
class MyNestedComponent(Component):
    name = "my_nested_component"

    @classmethod
    def get_schema(cls) -> type[MyNestedComponentSchema]:
        return MyNestedComponentSchema

    def build_defs(self, context: ComponentLoadContext) -> Definitions:
        return Definitions()
