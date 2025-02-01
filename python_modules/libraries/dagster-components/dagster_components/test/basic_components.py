"""Sample local components for testing validation. Paired with test cases
in integration_tests/components/validation.
"""

from dagster._core.definitions.definitions_class import Definitions
from pydantic import BaseModel, ConfigDict
from typing_extensions import Self

from dagster_components import Component, registered_component_type
from dagster_components.core.component import ComponentLoadContext


class MyComponentSchema(BaseModel):
    a_string: str
    an_int: int

    model_config = ConfigDict(extra="forbid")


@registered_component_type
class MyComponent(Component):
    name = "my_component"

    @classmethod
    def get_schema(cls) -> type[MyComponentSchema]:
        return MyComponentSchema

    @classmethod
    def load(cls, params: MyComponentSchema, context: ComponentLoadContext) -> Self:
        return cls()

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

    @classmethod
    def load(cls, params: MyComponentSchema, context: ComponentLoadContext) -> Self:
        return cls()

    def build_defs(self, context: ComponentLoadContext) -> Definitions:
        return Definitions()
