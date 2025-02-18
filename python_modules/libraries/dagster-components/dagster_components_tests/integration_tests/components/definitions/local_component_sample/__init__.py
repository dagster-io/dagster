from dagster._core.definitions.definitions_class import Definitions
from dagster_components import Component, ResolvableSchema, registered_component_type
from dagster_components.core.component import ComponentLoadContext


class MyComponentSchema(ResolvableSchema):
    a_string: str
    an_int: int


@registered_component_type
class MyComponent(Component):
    a_string: str
    an_int: int

    @classmethod
    def get_schema(cls):
        return MyComponentSchema

    def build_defs(self, context: ComponentLoadContext) -> Definitions:
        return Definitions()
