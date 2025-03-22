from dagster import asset
from dagster._core.definitions.definitions_class import Definitions
from dagster_components import Component, ComponentLoadContext
from dagster_components.core.component import component
from dagster_components_tests.integration_tests.some_resource import SomeResource


class NestedComponentThatMakesDecorator(Component):
    def build_defs(self, context: ComponentLoadContext) -> Definitions:
        assert "some_resource" in context.resources
        assert type(context.resources["some_resource"]).__name__ == "SomeResource"
        assert isinstance(context.resources["some_resource"], SomeResource)
        some_resource = context.resources["some_resource"]

        @asset
        def an_asset():
            return some_resource.get_value()

        return Definitions(assets=[an_asset])


@component
def load(context: ComponentLoadContext) -> NestedComponentThatMakesDecorator:
    """This component loads a Definitions object with no assets."""
    assert "some_resource" in context.resources
    assert isinstance(context.resources["some_resource"], SomeResource)
    return NestedComponentThatMakesDecorator()
