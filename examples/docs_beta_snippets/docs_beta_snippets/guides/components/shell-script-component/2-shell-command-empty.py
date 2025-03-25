from dagster import Definitions
from dagster_components import (
    Component,
    DefsModuleLoadContext,
    ResolvableModel,
)

class ShellCommand(Component, ResolvableModel):
    """COMPONENT SUMMARY HERE.

    COMPONENT DESCRIPTION HERE.
    """

    def build_defs(self, load_context: DefsModuleLoadContext) -> Definitions:
        # Add definition construction logic here.
        return Definitions()
