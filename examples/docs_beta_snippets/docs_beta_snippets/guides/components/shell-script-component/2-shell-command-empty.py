from dagster import Definitions
from dagster_components import (
    Component,
    ComponentLoadContext,
    DefaultComponentScaffolder,
    ResolvableSchema,
    registered_component_type,
)

class ShellCommandSchema(ResolvableSchema):
    ...

@registered_component_type(name="shell_command")
class ShellCommand(Component):
    """COMPONENT SUMMARY HERE.

    COMPONENT DESCRIPTION HERE.
    """

    @classmethod
    def get_schema(cls):
        return ShellCommandSchema

    @classmethod
    def get_scaffolder(cls) -> DefaultComponentScaffolder:
        return DefaultComponentScaffolder()

    def build_defs(self, load_context: ComponentLoadContext) -> Definitions:
        # Add definition construction logic here.
        return Definitions()
