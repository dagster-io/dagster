from pathlib import Path
from typing import Optional

from dagster._core.definitions.definitions_class import Definitions

from dagster_components_tests.integration_tests.component_loader import (
    build_defs_from_component_path,
    load_test_component_project_registry,
)
from dagster_components_tests.utils import inject_component


def load_test_component_defs_inject_component(
    src_path: str, local_component_defn_to_inject: Optional[Path]
) -> Definitions:
    """Loads a component from a test component project, making the provided local component defn
    available in that component's __init__.py.
    """
    with inject_component(
        src_path=src_path, local_component_defn_to_inject=local_component_defn_to_inject
    ) as tmpdir:
        registry = load_test_component_project_registry(include_test=True)

        return build_defs_from_component_path(
            path=Path(tmpdir),
            registry=registry,
            resources={},
        )
