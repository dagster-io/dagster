from pathlib import Path

import dagster as dg

MY_PYTHON_DEFS_COMPONENT_PATH = Path(__file__).parent.parent / "my_python_defs"


class MyCustomComponent(dg.Component):
    def build_defs(self, context: dg.ComponentLoadContext) -> dg.Definitions:
        assets_from_my_python_defs = context.component_tree.build_defs_at_path(
            MY_PYTHON_DEFS_COMPONENT_PATH
        ).resolve_all_asset_keys()

        @dg.asset(deps=assets_from_my_python_defs)
        def downstream_of_all_my_python_defs():
            pass

        return dg.Definitions(assets=[downstream_of_all_my_python_defs])
