import sys
from pathlib import Path
from typing import Optional

from dagster._core.definitions.definitions_class import Definitions
from dagster_components.core.component_defs_builder import MultiComponentsLoadContext

from dagster_components_tests.utils import create_project_from_components


def load_test_component_defs(
    src_path: str, local_component_defn_to_inject: Optional[Path] = None
) -> Definitions:
    """Loads a component from a test component project, making the provided local component defn
    available in that component's __init__.py.
    """
    with create_project_from_components(
        src_path, local_component_defn_to_inject=local_component_defn_to_inject
    ) as code_location_dir:
        sys.path.append(str(code_location_dir))

        return MultiComponentsLoadContext(resources={}).build_defs_from_component_path(
            path=Path(code_location_dir) / "my_location" / "defs" / Path(src_path).stem,
        )
