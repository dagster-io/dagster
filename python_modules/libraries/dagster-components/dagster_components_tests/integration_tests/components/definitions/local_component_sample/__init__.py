from dagster._core.definitions.definitions_class import Definitions
from dagster_components import Component, registered_component_type
from dagster_components.core.component import ComponentLoadContext
from dagster_components.core.schema.base import BaseModel
from typing_extensions import Self


class MyComponentSchema(BaseModel):
    a_string: str
    an_int: int


@registered_component_type
class MyComponent(Component):
    name = "my_component"

    @classmethod
    def get_schema(cls):
        return MyComponentSchema

    @classmethod
    def load(cls, params: MyComponentSchema, context: ComponentLoadContext) -> Self:
        return cls()

    def build_defs(self, context: ComponentLoadContext) -> Definitions:
        return Definitions()
