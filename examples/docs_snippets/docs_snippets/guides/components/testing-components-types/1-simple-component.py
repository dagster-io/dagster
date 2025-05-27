import dagster as dg
from dagster.components import Component, ComponentLoadContext, Model


class SimpleComponent(Component, Model):
    value: int

    def build_defs(self, context: ComponentLoadContext) -> dg.Definitions:
        @dg.asset
        def an_asset() -> int:
            return self.value

        return dg.Definitions([an_asset])
