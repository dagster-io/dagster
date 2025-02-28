from collections.abc import Sequence
from pathlib import Path
from typing import cast

import dagster as dg
from dagster._core.definitions.assets import AssetsDefinition
from dagster_components.core.component import ComponentLoadContext

DBT_COMPONENT_PATH = Path(__file__).parent.parent / "my_python_defs"

ctx = ComponentLoadContext.current()

assets_from_my_python_defs = cast(
    Sequence[AssetsDefinition], ctx.build_defs_from_component_path(DBT_COMPONENT_PATH).assets
)


@dg.asset(deps=assets_from_my_python_defs)
def downstream_of_all_my_python_defs():
    pass
