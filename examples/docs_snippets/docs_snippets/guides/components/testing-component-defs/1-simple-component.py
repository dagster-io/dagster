import dagster as dg
from dagster.components import Component, ComponentLoadContext, Model, Resolvable


class SimpleComponent(Component, Model, Resolvable):
    asset_key: str
    value: str

    # added fields here will define yaml schema via Model

    def build_defs(self, context: ComponentLoadContext) -> dg.Definitions:
        @dg.asset(key=self.asset_key)
        def the_asset() -> str:
            return self.value

        return dg.Definitions([the_asset])
