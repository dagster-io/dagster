from dagster._core.definitions.definitions_class import Definitions
from dagster.components import Component, ComponentLoadContext
from pydantic import BaseModel


class MyNewComponentSchema(BaseModel):
    a_string: str
    an_int: int


class MyNewComponent(Component):
    @classmethod
    def get_model_cls(cls):
        return MyNewComponentSchema

    def build_defs(self, context: ComponentLoadContext) -> Definitions:
        return Definitions()
