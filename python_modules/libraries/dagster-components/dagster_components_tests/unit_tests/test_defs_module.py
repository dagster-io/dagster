from dagster import asset
from dagster_components.core.component import (
    Component,
    ComponentLoadContext,
    Definitions,
    DefsLoader,
    defs_module,
)


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
