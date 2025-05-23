import dagster as dg


class ShellCommand(dg.Component, dg.Model, dg.Resolvable):
    """COMPONENT SUMMARY HERE.

    COMPONENT DESCRIPTION HERE.
    """

    # added fields here will define yaml schema via Model

    def build_defs(self, context: dg.ComponentLoadContext) -> dg.Definitions:
        # Add definition construction logic here.
        return dg.Definitions()
