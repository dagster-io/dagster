from dagster import asset
from dagster._core.definitions.definitions_class import Definitions
from dagster_components import Component, ComponentLoadContext
from dagster_components.core.component import component
from dagster_components_tests.integration_tests.some_resource import SomeResource
from dagster_shared.record import record


@record
class PeerComponent(Component):
    some_resource: SomeResource

    def build_defs(self, context: ComponentLoadContext) -> Definitions:
        @asset
        def peer_asset():
            return self.execute()

        return Definitions(assets=[peer_asset])

    def execute(self) -> str:
        return self.some_resource.value


@component
def load(context: ComponentLoadContext) -> PeerComponent:
    """This component loads a Definitions object with no assets."""
    assert "some_resource" in context.resources, "'some_resource' not found in context.resources"
    assert isinstance(context.resources["some_resource"], SomeResource)
    return PeerComponent(some_resource=context.resources["some_resource"])
