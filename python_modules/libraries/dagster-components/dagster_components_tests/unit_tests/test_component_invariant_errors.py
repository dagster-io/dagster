from dagster_components import Component, ComponentLoadContext


def test_component_does_not_implement_resolved_anything():
    class AComponent(Component):
        def build_defs(self, context): ...  # pyright: ignore[reportIncompatibleMethodOverride]

    assert AComponent.load(attributes=None, context=ComponentLoadContext.for_test())
