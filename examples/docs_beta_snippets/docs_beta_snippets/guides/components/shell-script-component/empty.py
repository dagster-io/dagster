from dagster_components import Component, DefsModuleLoadContext, ResolvableModel
from pydantic import BaseModel

import dagster as dg


class ShellCommand(Component, ResolvableModel):
    def build_defs(self, load_context: DefsModuleLoadContext) -> dg.Definitions: ...
