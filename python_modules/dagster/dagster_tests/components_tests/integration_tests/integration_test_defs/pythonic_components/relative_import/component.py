import dagster as dg
from dagster import ComponentLoadContext

# This import is used to test relative imports in the same module.
from .other_file import return_value  # noqa


class AComponent(dg.Component):
    """A simple component class for demonstration purposes."""

    def build_defs(self, context: ComponentLoadContext) -> dg.Definitions:
        assert return_value() == "value", "Expected return_value to be 'value'"

        @dg.asset(key=return_value())
        def an_asset() -> None: ...

        return dg.Definitions(assets=[an_asset])


@dg.component_instance
def load(context: ComponentLoadContext) -> dg.Component:
    """A component that loads a component from the same module."""
    return AComponent()
