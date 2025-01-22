from dagster._core.definitions.definitions_class import Definitions
from dagster_components import Component, component_type
from dagster_components.core.component import ComponentLoadContext
from dagster_components.core.schema.base import ComponentSchemaBaseModel
from typing_extensions import Self


class MyNewComponentSchema(ComponentSchemaBaseModel):
    a_string: str
    an_int: int


@component_type
class MyNewComponent(Component):
    name = "my_new_component"

    @classmethod
    def get_schema(cls):
        return MyNewComponentSchema

    @classmethod
    def load(cls, context: ComponentLoadContext) -> Self:
        context.load_params(MyNewComponentSchema)
        return cls()

    def build_defs(self, context: ComponentLoadContext) -> Definitions:
        return Definitions()
