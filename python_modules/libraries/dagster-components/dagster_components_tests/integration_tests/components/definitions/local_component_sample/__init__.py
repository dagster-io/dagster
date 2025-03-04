from dagster._core.definitions.definitions_class import Definitions
from dagster_components import Component
from dagster_components.core.component import ComponentLoadContext
from dagster_components.core.schema.base import PlainSamwiseSchema


class MyComponentSchema(PlainSamwiseSchema):
    a_string: str
    an_int: int


class MyComponent(Component):
    a_string: str
    an_int: int

    @classmethod
    def get_schema(cls):
        return MyComponentSchema

    def build_defs(self, context: ComponentLoadContext) -> Definitions:
        return Definitions()
