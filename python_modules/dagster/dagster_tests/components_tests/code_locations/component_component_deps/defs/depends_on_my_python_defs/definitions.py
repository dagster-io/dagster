from pathlib import Path

import dagster as dg
from dagster.components.core.context import ComponentLoadContext


@dg.definitions
def defs(context: ComponentLoadContext) -> dg.Definitions:
    @dg.asset(
        deps=context.component_tree.build_defs_at_path(
            Path("my_python_defs")
        ).resolve_all_asset_specs()
    )
    def downstream_of_all_my_python_defs(): ...

    return dg.Definitions(assets=[downstream_of_all_my_python_defs])
