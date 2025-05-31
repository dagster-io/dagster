from typing import TYPE_CHECKING, cast

import dagster as dg
from dagster.components.core.context import ComponentLoadContext

if TYPE_CHECKING:
    from collections.abc import Sequence


@dg.definitions
def defs(context: ComponentLoadContext) -> dg.Definitions:
    from component_component_deps.defs import my_python_defs  # type:ignore

    @dg.asset(
        deps=cast(
            "Sequence[dg.AssetsDefinition]",
            context.load_defs(my_python_defs).assets,
        )
    )
    def downstream_of_all_my_python_defs(): ...

    return dg.Definitions(assets=[downstream_of_all_my_python_defs])
