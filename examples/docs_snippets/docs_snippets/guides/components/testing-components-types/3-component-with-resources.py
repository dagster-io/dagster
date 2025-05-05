from dataclasses import dataclass

import dagster as dg
from dagster.components import Component, ComponentLoadContext, Model


@dataclass
class AResource:
    value: int


class SimpleComponent(Component, Model):
    def build_defs(self, context: ComponentLoadContext) -> dg.Definitions:
        @dg.asset
        def an_asset(a_resource: dg.ResourceParam[AResource]) -> int:
            return a_resource.value

        return dg.Definitions([an_asset])
