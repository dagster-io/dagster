from dagster_components import Component, ComponentLoadContext, DSLSchema
from pydantic import BaseModel

import dagster as dg


class ShellCommand(Component, DSLSchema):
    def build_defs(self, load_context: ComponentLoadContext) -> dg.Definitions: ...
