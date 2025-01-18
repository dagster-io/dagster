from dagster_components import (
    Component,
    ComponentLoadContext,
    ComponentSchemaBaseModel,
    component_type,
)

from dagster import Definitions


@component_type(name="shell_command")
class ShellCommand(Component):
    @classmethod
    def get_schema(cls) -> type[ComponentSchemaBaseModel]: ...

    def build_defs(self, load_context: ComponentLoadContext) -> Definitions: ...
