from typing import TypeVar

from dagster import asset
from dagster._core.definitions.asset_key import AssetKey
from dagster_components import ResolvableModel
from dagster_components.core.component import (
    Component,
    ComponentLoadContext,
    Definitions,
    DefsLoader,
    defs_module,
)
from pydantic import TypeAdapter


def test_simple_component_defs():
    class SimpleComponent(Component):
        def build_defs(self, context: ComponentLoadContext) -> Definitions:
            @asset
            def an_asset() -> None: ...

            return Definitions(assets=[an_asset])

    @defs_module()
    def loader(context: ComponentLoadContext) -> SimpleComponent:
        return SimpleComponent()

    context = ComponentLoadContext.for_test()
    definitions = loader.load_definitions(context)
    assert definitions.get_assets_def("an_asset")
    assert len(definitions.get_all_asset_specs()) == 1


def test_eager_definitions():
    @asset
    def an_asset() -> None: ...

    @defs_module()
    def loader(context: ComponentLoadContext) -> DefsLoader:
        return DefsLoader.for_eager_definitions(Definitions(assets=[an_asset]))

    context = ComponentLoadContext.for_test()
    definitions = loader.load_definitions(context)
    assert definitions.get_assets_def("an_asset")


def test_tags():
    @asset
    def an_asset() -> None: ...

    @defs_module(tags={"tag1": "value1"})
    def loader(context: ComponentLoadContext) -> DefsLoader:
        return DefsLoader.for_eager_definitions(Definitions(assets=[an_asset]))

    assert loader.tags == {"tag1": "value1"}


# T_Resolvable

from dagster_shared import check

T = TypeVar("T")


def from_defs_module(context: ComponentLoadContext, as_type: type[T]) -> T:
    check.param_invariant(context.defs_module, "context", "context must have a defs_module")
    assert context.defs_module
    check.param_invariant(
        context.defs_module.attributes, "context", "Must have defs_module.attributes"
    )
    assert context.defs_module.attributes is not None
    return TypeAdapter(as_type).validate_python(context.defs_module.attributes)


def test_attibutes():
    class SimpleModelComponent(ResolvableModel, Component):
        value: str

        def build_defs(self, context: ComponentLoadContext) -> Definitions:
            @asset(tags={"tag1": self.value})
            def my_asset() -> None: ...

            return Definitions(assets=[my_asset])

    @defs_module(attributes={"value": "value1"})
    def loader(context: ComponentLoadContext) -> SimpleModelComponent:
        return from_defs_module(context, SimpleModelComponent)

    context = ComponentLoadContext.for_test()
    definitions = loader.load_definitions(context)
    specs = {spec.key: spec for spec in definitions.get_all_asset_specs()}
    assert specs[AssetKey("my_asset")].tags == {"tag1": "value1"}
