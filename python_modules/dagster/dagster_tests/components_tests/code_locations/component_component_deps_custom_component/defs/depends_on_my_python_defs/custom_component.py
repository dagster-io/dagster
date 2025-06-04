from pathlib import Path
from typing import TYPE_CHECKING, cast

import dagster as dg

if TYPE_CHECKING:
    from collections.abc import Sequence

MY_PYTHON_DEFS_COMPONENT_PATH = Path(__file__).parent.parent / "my_python_defs"


class MyCustomComponent(dg.Component):
    def build_defs(self, context: dg.ComponentLoadContext) -> dg.Definitions:
        assets_from_my_python_defs = cast(
            "Sequence[dg.AssetKey]",
            context.component_tree.get_all_asset_keys_at_path(
                MY_PYTHON_DEFS_COMPONENT_PATH.absolute()
            ),
        )

        @dg.asset(deps=assets_from_my_python_defs)
        def downstream_of_all_my_python_defs():
            pass

        return dg.Definitions(assets=[downstream_of_all_my_python_defs])
