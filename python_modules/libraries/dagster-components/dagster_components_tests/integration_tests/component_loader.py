import importlib
from pathlib import Path
from typing import Optional

from dagster._core.definitions.definitions_class import Definitions
from dagster_components.core.component_defs_builder import DefinitionsModuleCache

from dagster_components_tests.utils import create_project_from_components


def load_test_component_defs(
    src_path: str, local_component_defn_to_inject: Optional[Path] = None
) -> Definitions:
    """Loads a component from a test component project, making the provided local component defn
    available in that component's __init__.py.
    """
    with create_project_from_components(
        src_path, local_component_defn_to_inject=local_component_defn_to_inject
    ) as (_, project_name):
        module = importlib.import_module(f"{project_name}.defs.{Path(src_path).stem}")

        return DefinitionsModuleCache(resources={}).load_defs(module=module)
