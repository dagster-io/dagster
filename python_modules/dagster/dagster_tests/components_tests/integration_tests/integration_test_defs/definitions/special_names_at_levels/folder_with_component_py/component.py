from dagster import Component, ComponentLoadContext, component_instance
from dagster._core.definitions.decorators.asset_decorator import asset
from dagster._core.definitions.definitions_class import Definitions


class AComponent(Component):
    """A simple component class for demonstration purposes."""

    def build_defs(self, context: ComponentLoadContext) -> Definitions:
        @asset
        def asset_in_component_py() -> None: ...

        return Definitions(assets=[asset_in_component_py])


@component_instance
def load(context: ComponentLoadContext) -> Component:
    """A component that loads a component from the same module."""
    return AComponent()
