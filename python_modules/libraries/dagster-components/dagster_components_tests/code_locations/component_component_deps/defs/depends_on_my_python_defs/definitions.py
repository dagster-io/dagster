from collections.abc import Sequence
from typing import cast

import dagster as dg
from component_component_deps.defs import my_python_defs
from dagster._core.definitions.assets import AssetsDefinition
from dagster_components.core.component import ComponentLoadContext

ctx = ComponentLoadContext.current()

assets_from_my_python_defs = cast(
    Sequence[AssetsDefinition],
    ctx.build_defs_from_component_module(my_python_defs).assets,
)


@dg.asset(deps=assets_from_my_python_defs)
def downstream_of_all_my_python_defs():
    pass
