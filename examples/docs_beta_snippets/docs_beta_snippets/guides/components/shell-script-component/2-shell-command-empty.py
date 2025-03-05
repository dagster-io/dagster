from dagster import Definitions
from dagster_components import (
    Component,
    ComponentLoadContext,
    YamlSchema,
)

class ShellCommand(Component, YamlSchema):
    """COMPONENT SUMMARY HERE.

    COMPONENT DESCRIPTION HERE.
    """

    def build_defs(self, load_context: ComponentLoadContext) -> Definitions:
        # Add definition construction logic here.
        return Definitions()
