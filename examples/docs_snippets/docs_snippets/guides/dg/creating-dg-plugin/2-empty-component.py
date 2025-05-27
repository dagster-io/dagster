from dataclasses import dataclass

import dagster as dg


@dataclass
class EmptyComponent(dg.Component, dg.Resolvable):
    """A component that does nothing."""

    def build_defs(self, context: dg.ComponentLoadContext) -> dg.Definitions:
        return dg.Definitions()
