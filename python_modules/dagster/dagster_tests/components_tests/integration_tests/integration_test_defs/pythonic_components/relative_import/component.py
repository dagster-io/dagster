from dagster._core.definitions.decorators.asset_decorator import asset
from dagster._core.definitions.definitions_class import Definitions
from dagster.components import Component, ComponentLoadContext, component

# This import is used to test relative imports in the same module.
from .other_file import return_value  # noqa


class AComponent(Component):
    """A simple component class for demonstration purposes."""

    def build_defs(self, context: ComponentLoadContext) -> Definitions:
        assert return_value() == "value", "Expected return_value to be 'value'"

        @asset(key=return_value())
        def an_asset() -> None: ...

        return Definitions(assets=[an_asset])


@component
def load(context: ComponentLoadContext) -> Component:
    """A component that loads a component from the same module."""
    return AComponent()
