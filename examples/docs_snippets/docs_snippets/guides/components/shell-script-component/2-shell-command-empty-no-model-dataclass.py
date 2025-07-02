from dataclasses import dataclass

import dagster as dg


@dataclass
class ShellCommand(dg.Component, dg.Resolvable):
    """COMPONENT SUMMARY HERE.

    COMPONENT DESCRIPTION HERE.
    """

    # Add schema fields here

    def build_defs(self, context: dg.ComponentLoadContext) -> dg.Definitions:
        # Add definition construction logic here.
        return dg.Definitions()
