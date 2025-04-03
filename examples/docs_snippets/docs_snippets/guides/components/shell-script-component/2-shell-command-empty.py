from dagster import Definitions
from dagster.components import (
    Component,
    ComponentLoadContext,
    Resolvable,
)
from dataclasses import dataclass


@dataclass
class ShellCommand(Component, Resolvable):
    """COMPONENT SUMMARY HERE.

    COMPONENT DESCRIPTION HERE.
    """

    def build_defs(self, context: ComponentLoadContext) -> Definitions:
        # Add definition construction logic here.
        return Definitions()
