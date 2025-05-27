from pathlib import Path
from typing import Optional

from dagster._core.definitions.definitions_class import Definitions
from dagster.components.core.context import ComponentLoadContext
from dagster.components.test.build_components import build_component_defs_at_defs_path


def get_dagster_test_project_root() -> Path:
    return Path(__file__).parent.parent.parent.parent.parent / "dagster-test"


def get_dagster_test_component_load_context(
    defs_path: Optional[Path] = None,
) -> ComponentLoadContext:
    import dagster_test.dg_defs

    context = ComponentLoadContext.for_module(dagster_test.dg_defs, get_dagster_test_project_root())
    return context.for_defs_path(defs_path) if defs_path else context


def get_dagster_relative_path(module_root_path: Path, path: Path) -> Path:
    relative_path = path.relative_to(module_root_path)
    if relative_path.suffix == ".py":
        relative_path = relative_path.with_suffix("")

    return relative_path


def defs_path_in_dagster_test_project(module_root_path: Path, dunderfile_path: Path) -> Path:
    return get_dagster_relative_path(module_root_path, dunderfile_path)


def defs_for_test_file(module_root_path: Path, dunderfile_path: Path) -> Definitions:
    return build_component_defs_at_defs_path(
        get_dagster_test_component_load_context(),
        defs_path=defs_path_in_dagster_test_project(
            module_root_path,
            dunderfile_path,
        ),
    )
