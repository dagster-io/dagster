from dagster import (
    AssetSpec,
    Component,
    ComponentLoadContext,
    Definitions,
    Resolvable,
    build_defs_for_component,
)
from dagster_shared.record import record


@record
class MyComponent(Component, Resolvable):
    asset_key: str

    def build_defs(self, context: ComponentLoadContext) -> Definitions:
        return Definitions(assets=[AssetSpec(key=self.asset_key)])


def test_build_defs_for_component_basic():
    component = MyComponent.from_attributes_dict(attributes={"asset_key": "asset1"})

    defs = build_defs_for_component(component=component)
    assert defs.assets == [AssetSpec(key="asset1")]
