from typing import TYPE_CHECKING, cast

import dagster as dg
from component_component_deps.defs import my_python_defs  # type:ignore
from dagster.components.core.context import ComponentLoadContext

if TYPE_CHECKING:
    from collections.abc import Sequence

    from dagster._core.definitions.assets import AssetsDefinition

ctx = ComponentLoadContext.current()


@dg.asset(
    deps=cast(
        "Sequence[AssetsDefinition]",
        ctx.load_defs(my_python_defs).assets,
    )
)
def downstream_of_all_my_python_defs():
    pass
