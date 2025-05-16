from pathlib import Path
from typing import Optional

from dagster.components.core.context import ComponentLoadContext


def get_dagster_test_project_root() -> Path:
    return Path(__file__).parent.parent.parent.parent.parent / "dagster-test"


def get_dagster_test_component_load_context(
    defs_path: Optional[Path] = None,
) -> ComponentLoadContext:
    import dagster_test.dg_defs

    context = ComponentLoadContext.for_module(dagster_test.dg_defs, get_dagster_test_project_root())
    return context.for_defs_path(defs_path) if defs_path else context
