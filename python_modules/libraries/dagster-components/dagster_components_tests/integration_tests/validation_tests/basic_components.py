"""Sample local components for testing validation. Paired with test cases
in integration_tests/components/validation.
"""

from dagster._core.definitions.definitions_class import Definitions
from dagster_components import Component, component_type
from dagster_components.core.component import ComponentLoadContext
from dagster_components.core.schema.base import ComponentSchemaBaseModel
from typing_extensions import Self


class MyComponentSchema(ComponentSchemaBaseModel):
    a_string: str
    an_int: int


@component_type
class MyComponent(Component):
    name = "my_component"
    params_schema = MyComponentSchema

    @classmethod
    def load(cls, context: ComponentLoadContext) -> Self:
        context.load_params(cls.params_schema)
        return cls()

    def build_defs(self, context: ComponentLoadContext) -> Definitions:
        return Definitions()


class MyNestedModel(ComponentSchemaBaseModel):
    a_string: str
    an_int: int


class MyNestedComponentSchema(ComponentSchemaBaseModel):
    nested: dict[str, MyNestedModel]


@component_type
class MyNestedComponent(Component):
    name = "my_nested_component"
    params_schema = MyNestedComponentSchema

    @classmethod
    def load(cls, context: ComponentLoadContext) -> Self:
        context.load_params(cls.params_schema)
        return cls()

    def build_defs(self, context: ComponentLoadContext) -> Definitions:
        return Definitions()
