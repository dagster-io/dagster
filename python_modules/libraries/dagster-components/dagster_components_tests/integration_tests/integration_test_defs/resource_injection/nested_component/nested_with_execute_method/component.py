from dagster import asset
from dagster._core.definitions.definitions_class import Definitions
from dagster_components import Component, ComponentLoadContext
from dagster_components.core.component import component
from dagster_components_tests.integration_tests.some_resource import SomeResource
from dagster_shared.record import record


@record
class NestedComponent(Component):
    some_resource: SomeResource

    def build_defs(self, context: ComponentLoadContext) -> Definitions:
        @asset
        def an_asset_calls_execute():
            return self.execute()

        return Definitions(assets=[an_asset_calls_execute])

    def execute(self) -> str:
        return self.some_resource.get_value()


@component
def load(context: ComponentLoadContext) -> NestedComponent:
    """This component loads a Definitions object with no assets."""
    assert "some_resource" in context.resources
    assert type(context.resources["some_resource"]).__name__ == "SomeResource"
    assert isinstance(context.resources["some_resource"], SomeResource)
    return NestedComponent(some_resource=context.resources["some_resource"])
