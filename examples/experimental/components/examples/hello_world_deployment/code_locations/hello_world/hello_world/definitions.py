from pathlib import Path

from dagster._components import ComponentRegistry, build_defs_from_toplevel_components_folder
from dagster._components.impls.python_script_component import PythonScriptCollection
from dagster._core.pipes.subprocess import PipesSubprocessClient

defs = build_defs_from_toplevel_components_folder(
    path=Path(__file__).parent,
    registry=ComponentRegistry({"python_script_collection": PythonScriptCollection}),
    resources={"pipes_client": PipesSubprocessClient()},
)
