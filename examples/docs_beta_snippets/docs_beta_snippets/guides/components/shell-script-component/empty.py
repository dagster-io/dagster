from dagster_components import Component, ComponentLoadContext
from pydantic import BaseModel

import dagster as dg


class ShellCommand(Component):
    def build_defs(self, load_context: ComponentLoadContext) -> dg.Definitions: ...
