from pathlib import Path

import dagster as dg
from dagster_components import ComponentTypeRegistry, build_component_defs
from dagster_components.lib.pipes_subprocess_script_collection import (
    PipesSubprocessScriptCollection,
)

defs = build_component_defs(
    Path(__file__).parent / "components",
    registry=ComponentTypeRegistry(
        {"pipes_subprocess_script_collection": PipesSubprocessScriptCollection}
    ),
)

if __name__ == "__main__":
    dg.Definitions.validate_loadable(defs)
