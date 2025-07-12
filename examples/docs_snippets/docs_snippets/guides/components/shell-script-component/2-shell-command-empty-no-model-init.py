import dagster as dg


class ShellCommand(dg.Component, dg.Resolvable):
    """COMPONENT SUMMARY HERE.

    COMPONENT DESCRIPTION HERE.
    """

    def __init__(
        self,
        # added arguments here will define yaml schema via Resolvable
    ):
        pass

    def build_defs(self, context: dg.ComponentLoadContext) -> dg.Definitions:
        # Add definition construction logic here.
        return dg.Definitions()
