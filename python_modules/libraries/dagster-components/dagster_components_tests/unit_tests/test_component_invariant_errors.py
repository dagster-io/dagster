from dagster_components import Component, DefsLoadContext


def test_component_does_not_implement_resolved_anything():
    class AComponent(Component):
        def build_defs(self, context): ...

    assert AComponent.load(attributes=None, context=DefsLoadContext.for_test())
