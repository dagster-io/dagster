from pathlib import Path

from dagster.components.core.context import ComponentLoadContext


def get_dagster_test_project_root() -> Path:
    return Path(__file__).parent.parent.parent.parent.parent / "dagster-test"


def get_dagster_test_component_load_context() -> ComponentLoadContext:
    import dagster_test.dg_defs

    return ComponentLoadContext.for_module(dagster_test.dg_defs, get_dagster_test_project_root())
