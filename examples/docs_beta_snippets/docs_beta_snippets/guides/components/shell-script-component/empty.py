from dagster_components import (
    Component,
    ComponentLoadContext,
    ResolvableSchema,
    registered_component_type,
)
from pydantic import BaseModel

import dagster as dg


@registered_component_type(name="shell_command")
class ShellCommand(Component):
    @classmethod
    def get_schema(cls) -> type[ResolvableSchema]: ...

    def build_defs(self, load_context: ComponentLoadContext) -> dg.Definitions: ...
