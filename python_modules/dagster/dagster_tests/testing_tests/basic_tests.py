from dataclasses import dataclass
from pathlib import Path

import dagster as dg
from dagster.components.component.component import Component
from dagster.components.core.context import ComponentLoadContext


def test_basic_test() -> None:
    class SimpleComponent(dg.Component):
        def build_defs(self, context: ComponentLoadContext) -> dg.Definitions:
            @dg.asset
            def an_asset() -> int:
                return 1

            return dg.Definitions([an_asset])

    an_asset = dg.component_defs(component=SimpleComponent()).resolve_assets_def("an_asset")

    assert an_asset.key == dg.AssetKey("an_asset")
    assert an_asset() == 1


def test_asset_with_resources() -> None:
    @dataclass
    class AResource:
        value: str

    class ComponentWithUnfulfilledResource(dg.Component):
        def build_defs(self, context: ComponentLoadContext) -> dg.Definitions:
            @dg.asset
            def asset_with_resource(a_resource: dg.ResourceParam[AResource]) -> str:
                return a_resource.value

            return dg.Definitions([asset_with_resource])

    an_asset = dg.component_defs(
        component=ComponentWithUnfulfilledResource(),
        resources={"a_resource": AResource(value="foo")},
    ).resolve_assets_def("asset_with_resource")

    assert isinstance(an_asset, dg.AssetsDefinition)
    assert an_asset() == "foo"


def test_components_with_declaration():
    class ModelComponentWithDeclaration(dg.Component, dg.Model, dg.Resolvable):
        value: str

        def build_defs(self, context: ComponentLoadContext) -> dg.Definitions:
            @dg.asset
            def an_asset() -> str:
                return self.value

            return dg.Definitions([an_asset])

    assert (
        dg.component_defs(component=ModelComponentWithDeclaration(value="bar")).resolve_assets_def(
            "an_asset"
        )()
        == "bar"
    )

    assert (
        dg.component_defs(
            component=ModelComponentWithDeclaration.from_attributes_dict(
                attributes={"value": "foobar"}
            ),
        ).resolve_assets_def("an_asset")()
        == "foobar"
    )

    class ManualInitComponentWithDeclaration(dg.Component, dg.Resolvable):
        def __init__(self, value: str):
            self._value = value

        @property
        def value(self) -> str:
            return self._value

        def build_defs(self, context: ComponentLoadContext) -> dg.Definitions:
            @dg.asset
            def an_asset() -> str:
                return self.value

            return dg.Definitions([an_asset])

    assert (
        dg.component_defs(
            component=ManualInitComponentWithDeclaration(value="bar")
        ).resolve_assets_def("an_asset")()
        == "bar"
    )

    assert (
        dg.component_defs(
            component=ManualInitComponentWithDeclaration.from_attributes_dict(
                attributes={"value": "foobar"}
            ),
        ).resolve_assets_def("an_asset")()
        == "foobar"
    )

    @dataclass
    class DataclassComponentWithDeclaration(dg.Component, dg.Resolvable):
        value: str

        def build_defs(self, context: ComponentLoadContext) -> dg.Definitions:
            @dg.asset
            def an_asset() -> str:
                return self.value

            return dg.Definitions([an_asset])

    assert (
        dg.component_defs(
            component=DataclassComponentWithDeclaration(value="bar")
        ).resolve_assets_def("an_asset")()
        == "bar"
    )

    assert (
        dg.component_defs(
            component=DataclassComponentWithDeclaration.from_attributes_dict(
                attributes={"value": "foobar"}
            ),
        ).resolve_assets_def("an_asset")()
        == "foobar"
    )


def test_component_on_disk():
    path = Path(__file__).parent / "some_value_simple_asset_component.yaml"
    assets_def = dg.component_defs(component=Component.from_yaml_path(path)).resolve_assets_def(
        "an_asset"
    )
    assert assets_def(context=dg.build_asset_context()) == "some_value"
