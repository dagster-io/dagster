from collections.abc import Sequence
from pathlib import Path
from typing import cast

import dagster as dg
from dagster_components import Component
from dagster_components.core.component import ComponentLoadContext

MY_PYTHON_DEFS_COMPONENT_PATH = Path(__file__).parent.parent / "my_python_defs"


class MyCustomComponent(Component):
    def build_defs(self, context: ComponentLoadContext) -> dg.Definitions:
        assets_from_my_python_defs = cast(
            Sequence[dg.AssetsDefinition],
            context.build_defs_from_component_path(MY_PYTHON_DEFS_COMPONENT_PATH).assets,
        )

        @dg.asset(deps=assets_from_my_python_defs)
        def downstream_of_all_my_python_defs():
            pass

        return dg.Definitions(assets=[downstream_of_all_my_python_defs])
