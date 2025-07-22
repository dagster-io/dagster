import dagster as dg
from dagster import ComponentLoadContext


class AComponent(dg.Component):
    """A simple component class for demonstration purposes."""

    def build_defs(self, context: ComponentLoadContext) -> dg.Definitions:
        @dg.asset
        def asset_in_component_py() -> None: ...

        return dg.Definitions(assets=[asset_in_component_py])


@dg.component_instance
def load(context: ComponentLoadContext) -> dg.Component:
    """A component that loads a component from the same module."""
    return AComponent()
