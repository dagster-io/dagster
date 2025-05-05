import importlib
from pathlib import Path
from types import ModuleType
from typing import Optional

from dagster_shared.serdes.objects.package_entry import json_for_all_components

from dagster._annotations import deprecated, preview, public
from dagster._core.definitions.definitions_class import Definitions
from dagster._core.errors import DagsterInvalidDefinitionError
from dagster._utils.warnings import suppress_dagster_warnings
from dagster.components.core.context import ComponentLoadContext, use_component_load_context

PLUGIN_COMPONENT_TYPES_JSON_METADATA_KEY = "plugin_component_types_json"


@deprecated(breaking_version="0.2.0")
@suppress_dagster_warnings
def build_component_defs(components_root: Path) -> Definitions:
    """Build a Definitions object for all the component instances in a given code location.

    Args:
        components_root (Path): The path to the components root. This is a directory containing
            subdirectories with component instances.
    """
    defs_root = importlib.import_module(
        f"{Path(components_root).parent.name}.{Path(components_root).name}"
    )

    return load_defs(defs_root=defs_root, project_root=components_root.parent.parent)


def get_project_root(defs_root: ModuleType) -> Path:
    """Find the project root directory containing pyproject.toml or setup.py.

    Args:
        defs_root: A module object from which to start the search.

    Returns:
        The absolute path to the project root directory.

    Raises:
        FileNotFoundError: If no project root with pyproject.toml or setup.py is found.
    """
    # Get the module's file path

    module_path = getattr(defs_root, "__file__", None)
    if not module_path:
        raise FileNotFoundError(f"Module {defs_root} has no __file__ attribute")

    # Start with the directory containing the module
    current_dir = Path(module_path).parent

    # Traverse up until we find pyproject.toml or setup.py
    while current_dir != current_dir.parent:  # Stop at root
        if (current_dir / "pyproject.toml").exists() or (current_dir / "setup.py").exists():
            return current_dir
        current_dir = current_dir.parent

    raise FileNotFoundError("No project root with pyproject.toml or setup.py found")


# Public method so optional Nones are fine
@public
@preview(emit_runtime_warning=False)
@suppress_dagster_warnings
def load_defs(defs_root: ModuleType, project_root: Optional[Path] = None) -> Definitions:
    """Constructs a Definitions object, loading all Dagster defs in the given module.

    Args:
        defs_root (Path): The path to the defs root, typically `package.defs`.
        project_root (Optional[Path]): path to the project root directory.
    """
    from dagster.components.core.defs_module import get_component
    from dagster.components.core.package_entry import discover_entry_point_package_objects
    from dagster.components.core.snapshot import get_package_entry_snap

    project_root = project_root if project_root else get_project_root(defs_root)

    # create a top-level DefsModule component from the root module
    context = ComponentLoadContext.for_module(defs_root, project_root)
    with use_component_load_context(context):
        root_component = get_component(context)
        if root_component is None:
            raise DagsterInvalidDefinitionError("Could not resolve root module to a component.")

        library_objects = discover_entry_point_package_objects()
        snaps = [get_package_entry_snap(key, obj) for key, obj in library_objects.items()]
        components_json = json_for_all_components(snaps)

        return Definitions.merge(
            root_component.build_defs(context),
            Definitions(metadata={PLUGIN_COMPONENT_TYPES_JSON_METADATA_KEY: components_json}),
        )
