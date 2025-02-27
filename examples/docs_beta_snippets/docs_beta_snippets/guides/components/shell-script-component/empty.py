from dagster_components import Component, ComponentLoadContext, ResolvableSchema
from pydantic import BaseModel

import dagster as dg


class ShellCommand(Component):
    @classmethod
    def get_schema(cls) -> type[ResolvableSchema]: ...

    def build_defs(self, load_context: ComponentLoadContext) -> dg.Definitions: ...
