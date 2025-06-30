from dagster import Component
from dagster.components.core.tree import ComponentTree


def test_component_does_not_implement_resolved_anything():
    class AComponent(Component):
        def build_defs(self, context): ...  # pyright: ignore[reportIncompatibleMethodOverride]

    assert AComponent.load(attributes=None, context=ComponentTree.for_test().load_context)
