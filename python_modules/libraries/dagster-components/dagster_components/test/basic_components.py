"""Sample local components for testing validation. Paired with test cases
in integration_tests/components/validation.
"""

from dagster._core.definitions.definitions_class import Definitions

from dagster_components import Component, YamlSchema
from dagster_components.core.component import ComponentLoadContext


class MyComponent(Component, YamlSchema):
    a_string: str
    an_int: int

    def build_defs(self, context: ComponentLoadContext) -> Definitions:
        return Definitions()


class MyNestedModel(YamlSchema):
    a_string: str
    an_int: int


class MyNestedComponent(Component, YamlSchema):
    nested: dict[str, MyNestedModel]

    def build_defs(self, context: ComponentLoadContext) -> Definitions:
        return Definitions()
