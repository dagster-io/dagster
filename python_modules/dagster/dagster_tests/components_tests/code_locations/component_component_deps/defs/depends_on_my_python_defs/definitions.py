from pathlib import Path

import dagster as dg
from dagster.components.core.context import ComponentLoadContext


@dg.definitions
def defs(context: ComponentLoadContext) -> dg.Definitions:
    @dg.asset(deps=context.component_tree.get_all_asset_keys_at_path(Path("my_python_defs")))
    def downstream_of_all_my_python_defs(): ...

    return dg.Definitions(assets=[downstream_of_all_my_python_defs])
