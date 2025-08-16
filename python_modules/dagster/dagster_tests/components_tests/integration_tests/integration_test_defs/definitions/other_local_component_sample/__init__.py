from pydantic import BaseModel

import dagster as dg


class MyNewComponentSchema(BaseModel):
    a_string: str
    an_int: int


class MyNewComponent(dg.Component):
    @classmethod
    def get_model_cls(cls):
        return MyNewComponentSchema

    def build_defs(self, context: dg.ComponentLoadContext) -> dg.Definitions:
        return dg.Definitions()
