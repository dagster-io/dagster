from collections.abc import Sequence

import dagster as dg
from dagster import AssetKey as AssetKey
from dagster_shared.record import record


@record
class MyCustomComponent(dg.Component, dg.Resolvable):
    deps: Sequence[dg.ResolvedAssetKey]

    def build_defs(self, context: dg.ComponentLoadContext) -> dg.Definitions:
        @dg.asset(deps=self.deps)
        def downstream_of_all_my_python_defs():
            pass

        return dg.Definitions(assets=[downstream_of_all_my_python_defs])
