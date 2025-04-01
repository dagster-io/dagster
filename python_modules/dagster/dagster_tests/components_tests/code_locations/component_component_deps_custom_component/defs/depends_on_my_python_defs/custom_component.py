from collections.abc import Sequence
from pathlib import Path
from typing import cast

import dagster as dg
from dagster.components import Component, ComponentLoadContext

MY_PYTHON_DEFS_COMPONENT_PATH = Path(__file__).parent.parent / "my_python_defs"


class MyCustomComponent(Component):
    def build_defs(self, context: ComponentLoadContext) -> dg.Definitions:
        from component_component_deps_custom_component.defs import my_python_defs  # type:ignore

        assets_from_my_python_defs = cast(
            Sequence[dg.AssetsDefinition],
            context.load_defs(my_python_defs).assets,
        )

        @dg.asset(deps=assets_from_my_python_defs)
        def downstream_of_all_my_python_defs():
            pass

        return dg.Definitions(assets=[downstream_of_all_my_python_defs])
