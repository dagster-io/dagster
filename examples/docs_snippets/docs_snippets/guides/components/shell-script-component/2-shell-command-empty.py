import dagster as dg
from dagster.components import Component, ComponentLoadContext, Model, Resolvable


@dataclass
class ShellCommand(Component, Model, Resolvable):
    """COMPONENT SUMMARY HERE.

    COMPONENT DESCRIPTION HERE.
    """

    # added fields here will define yaml schema via Resolvable

    def build_defs(self, context: ComponentLoadContext) -> dg.Definitions:
        # Add definition construction logic here.
        return dg.Definitions()
