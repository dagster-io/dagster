from dagster import Definitions
from dagster_components import (
    Component,
    ComponentLoadContext,
    DefaultComponentScaffolder,
    registered_component_type,
)
from pydantic import BaseModel

class ShellCommandParams(BaseModel):
    ...

@registered_component_type(name="shell_command")
class ShellCommand(Component):
    """COMPONENT SUMMARY HERE.

    COMPONENT DESCRIPTION HERE.
    """

    @classmethod
    def get_schema(cls):
        return ShellCommandParams

    @classmethod
    def get_scaffolder(cls) -> DefaultComponentScaffolder:
        return DefaultComponentScaffolder()

    @classmethod
    def load(
        cls,
        params: ShellCommandParams,
        context: ComponentLoadContext,
    ) -> "ShellCommand":
        # Add logic for mapping schema parameters to constructor args here.
        return cls()

    def build_defs(self, load_context: ComponentLoadContext) -> Definitions:
        # Add definition construction logic here.
        return Definitions()
