import dagster as dg
from dagster_components import Component, ComponentLoadContext, ResolvableModel


class MyBaseAssetsComponent(Component, ResolvableModel):
    def build_defs(self, context: ComponentLoadContext) -> dg.Definitions:
        @dg.asset
        def my_cool_asset():
            pass

        @dg.asset
        def my_other_cool_asset():
            pass

        return dg.Definitions(assets=[my_cool_asset, my_other_cool_asset])
