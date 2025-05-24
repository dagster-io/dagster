from dataclasses import dataclass

from dagster._core.definitions.asset_key import AssetKey
from dagster._core.definitions.assets import AssetsDefinition
from dagster._core.definitions.decorators.asset_decorator import asset
from dagster._core.definitions.definitions_class import Definitions
from dagster._core.definitions.resource_annotation import ResourceParam
from dagster.components.component.component import Component
from dagster.components.core.context import ComponentLoadContext
from dagster.components.testing import component_defs


def test_basic_test() -> None:
    class SimpleComponent(Component):
        def build_defs(self, context: ComponentLoadContext) -> Definitions:
            @asset
            def an_asset() -> int:
                return 1

            return Definitions([an_asset])

    an_asset = component_defs(component=SimpleComponent()).get_assets_def("an_asset")

    assert an_asset.key == AssetKey("an_asset")
    assert an_asset() == 1


def test_asset_with_resources() -> None:
    @dataclass
    class AResource:
        value: str

    class ComponentWithUnfulfilledResource(Component):
        def build_defs(self, context: ComponentLoadContext) -> Definitions:
            @asset
            def asset_with_resource(a_resource: ResourceParam[AResource]) -> str:
                return a_resource.value

            return Definitions([asset_with_resource])

    an_asset = component_defs(
        component=ComponentWithUnfulfilledResource(),
        resources={"a_resource": AResource(value="foo")},
    ).get_assets_def("asset_with_resource")

    assert isinstance(an_asset, AssetsDefinition)
    assert an_asset() == "foo"
