from dagster._core.definitions.definitions_class import Definitions
from dagster_components import Component, ComponentLoadContext
from pydantic import BaseModel


class MyNewComponentSchema(BaseModel):
    a_string: str
    an_int: int


class MyNewComponent(Component):
    name = "my_new_component"

    @classmethod
    def get_schema(cls):
        return MyNewComponentSchema

    def build_defs(self, context: ComponentLoadContext) -> Definitions:
        return Definitions()
