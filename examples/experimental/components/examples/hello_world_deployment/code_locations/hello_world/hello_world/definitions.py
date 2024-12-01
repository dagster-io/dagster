from pathlib import Path

from dagster._components import ComponentRegistry, build_defs_from_toplevel_components_folder
from dagster._components.impls.pipes_subprocess_script_collection import (
    PipesSubprocessScriptCollection,
)
from dagster._core.definitions.definitions_class import Definitions

defs = build_defs_from_toplevel_components_folder(
    path=Path(__file__).parent,
    registry=ComponentRegistry(
        {"pipes_subprocess_script_collection": PipesSubprocessScriptCollection}
    ),
)

if __name__ == "__main__":
    Definitions.validate_loadable(defs)
