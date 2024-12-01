from pathlib import Path

from dagster._components.core.component_defs_builder import ComponentLoadContext
from dagster._components.impls.pipes_subprocess_script_collection import (
    PipesSubprocessScriptCollection,
)
from dagster._core.definitions.asset_spec import AssetSpec


def component_path() -> Path:
    return Path(__file__).parent


# component = PipesSubprocessScriptCollection(
#     dirpath=component_path(),
#     path_specs={
#         component_path() / "script_one.py": [AssetSpec("asset_one")],
#         component_path() / "script_two.py": [AssetSpec("asset_two")],
#     },
# )

# defs = component.build_defs(
#     load_context=ComponentLoadContext(resources={}, registry=ComponentRegistry({}))
# )


def component_instance(context: ComponentLoadContext) -> PipesSubprocessScriptCollection:
    return PipesSubprocessScriptCollection(
        dirpath=component_path(),
        path_specs={
            component_path() / "script_one.py": [AssetSpec("asset_one")],
            component_path() / "script_two.py": [AssetSpec("asset_two")],
        },
    )
