from dagster import asset
from dagster._core.definitions.asset_key import AssetKey
from dagster._core.definitions.definitions_class import Definitions
from dagster_components import Component
from dagster_components.core.context import ComponentLoadContext
from dagster_components.lib.definitions_component.decorator import definitions_component
from dagster_components.test.utils import load_component_defs


def test_basic_definitions_component() -> None:
    @definitions_component
    def an_asset_component(context):
        @asset
        def an_asset() -> None: ...

        return Definitions([an_asset])

    assert isinstance(an_asset_component(ComponentLoadContext.for_test()), Component)
    defs = load_component_defs(component_fn=an_asset_component)
    assert isinstance(defs, Definitions)
    assert len(defs.get_all_asset_specs())
    assert defs.get_all_asset_specs()[0].key == AssetKey("an_asset")
