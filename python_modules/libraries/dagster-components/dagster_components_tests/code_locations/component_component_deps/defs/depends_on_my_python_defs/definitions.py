from typing import TYPE_CHECKING, cast

import dagster as dg
from component_component_deps.defs import my_python_defs  # type:ignore
from dagster_components.core.component import ComponentLoadContext

if TYPE_CHECKING:
    from collections.abc import Sequence

    from dagster._core.definitions.assets import AssetsDefinition

ctx = ComponentLoadContext.current()

assets_from_my_python_defs = cast(
    "Sequence[AssetsDefinition]",
    ctx.load_defs(my_python_defs).assets,
)


@dg.asset(deps=assets_from_my_python_defs)
def downstream_of_all_my_python_defs():
    pass
