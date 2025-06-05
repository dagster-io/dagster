import importlib
from pathlib import Path
from types import ModuleType
from typing import Optional

from dagster_shared import check
from dagster_shared.serdes.objects.package_entry import json_for_all_components

from dagster._annotations import deprecated, preview, public
from dagster._core.definitions.definitions_class import Definitions
from dagster._utils.warnings import suppress_dagster_warnings
from dagster.components.core.context import ComponentLoadContext
from dagster.components.core.tree import ComponentTree

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
def load_defs(
    defs_root: ModuleType,
    project_root: Optional[Path] = None,
    terminate_autoloading_on_keyword_files: bool = True,
) -> Definitions:
    """Constructs a Definitions object, loading all Dagster defs in the given module.

    Args:
        defs_root (Path): The path to the defs root, typically `package.defs`.
        project_root (Optional[Path]): path to the project root directory.
        terminate_autoloading_on_keyword_files (bool): Whether to terminate the defs
            autoloading process when encountering a definitions.py or component.py file.
            Defaults to True.
    """
    from dagster.components.core.defs_module import DefsFolderComponent, get_component

    project_root = project_root if project_root else get_project_root(defs_root)

    # create a top-level DefsModule component from the root module
    context = ComponentLoadContext.for_module(
        defs_root, project_root, terminate_autoloading_on_keyword_files
    )

    # Despite the argument being named defs_root, load_defs supports loading arbitrary components
    # directly, so use get_component instead of DefsFolderComponent.get
    root_component = check.not_none(
        get_component(context), "Could not resolve root module to a component."
    )

    # If we did get a folder component back, assume its the root tree
    tree = (
        ComponentTree(defs_module=defs_root, project_root=project_root)
        if isinstance(root_component, DefsFolderComponent)
        else None
    )

    return Definitions.merge(
        root_component.build_defs(context),
        get_library_json_enriched_defs(tree),
    )


def get_library_json_enriched_defs(tree: Optional[ComponentTree]) -> Definitions:
    from dagster.components.core.package_entry import discover_entry_point_package_objects
    from dagster.components.core.snapshot import get_package_entry_snap

    registry_objects = discover_entry_point_package_objects()
    snaps = [get_package_entry_snap(key, obj) for key, obj in registry_objects.items()]
    components_json = json_for_all_components(snaps)

    return Definitions(
        metadata={PLUGIN_COMPONENT_TYPES_JSON_METADATA_KEY: components_json},
        component_tree=tree,
    )
