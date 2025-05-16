from dataclasses import dataclass

import dagster as dg
from dagster.components import Component, ComponentLoadContext, Resolvable


@dataclass
class EmptyComponent(Component, Resolvable):
    """A component that does nothing."""

    def build_defs(self, context: ComponentLoadContext) -> dg.Definitions:
        return dg.Definitions()
