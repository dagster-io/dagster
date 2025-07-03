import dagster as dg
from dagster import ComponentLoadContext
from dagster_shared.record import record


@record
class MyComponent(dg.Component, dg.Resolvable):
    asset_key: str

    def build_defs(self, context: ComponentLoadContext) -> dg.Definitions:
        return dg.Definitions(assets=[dg.AssetSpec(key=self.asset_key)])


def test_build_defs_for_component_basic():
    component = MyComponent.from_attributes_dict(attributes={"asset_key": "asset1"})

    defs = dg.build_defs_for_component(component=component)
    assert defs.assets == [dg.AssetSpec(key="asset1")]
