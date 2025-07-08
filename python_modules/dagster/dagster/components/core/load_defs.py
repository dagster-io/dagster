import importlib
from pathlib import Path
from types import ModuleType
from typing import Optional

from dagster_shared import check
from dagster_shared.serdes.objects.package_entry import json_for_all_components
from dagster_shared.utils.config import (
    get_canonical_defs_module_name,
    load_toml_as_dict,
    locate_dg_config_in_folder,
)

from dagster._annotations import deprecated, public
from dagster._core.definitions.definitions_class import Definitions
from dagster._utils.warnings import suppress_dagster_warnings
from dagster.components.component.component import Component
from dagster.components.core.tree import ComponentTree, LegacyAutoloadingComponentTree

PLUGIN_COMPONENT_TYPES_JSON_METADATA_KEY = "plugin_component_types_json"


@deprecated(breaking_version="0.2.0")
@suppress_dagster_warnings
def build_component_defs(components_root: Path) -> Definitions:
    """Build a Definitions object for all the component instances in a given project.

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
    if module_path is None:
        # For modules without __file__ attribute (e.g. namespace packages), try to get path from __path__
        module_paths = getattr(defs_root, "__path__", None)
        if module_paths and len(module_paths) > 0:
            module_path = module_paths[0]
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


@public
@suppress_dagster_warnings
def build_defs_for_component(component: Component) -> Definitions:
    """Constructs Definitions from a standalone component. This is useful for
    loading individual components in a non-component project.

    Args:
        component (Component): The component to load defs from.
    """
    return component.build_defs(ComponentTree.for_test().load_context)


@public
@suppress_dagster_warnings
def load_from_defs_folder(*, project_root: Path) -> Definitions:
    """Constructs a Definitions object by automatically discovering and loading all Dagster
    definitions from a project's defs folder structure.

    This function serves as the primary entry point for loading definitions in dg-managed
    projects. It reads the project configuration (dg.toml or pyproject.toml), identifies
    the defs module, and recursively loads all components, assets, jobs, and other Dagster
    definitions from the project structure.

    The function automatically handles:

    * Reading project configuration to determine the defs module location
    * Importing and traversing the defs module hierarchy
    * Loading component definitions and merging them into a unified Definitions object
    * Enriching definitions with plugin component metadata from entry points

    Args:
        project_root (Path): The absolute path to the dg project root directory. This should be the directory containing the project's configuration file (dg.toml or pyproject.toml with [tool.dg] section).

    Returns:
        Definitions: A merged Definitions object containing all discovered definitions from the project's defs folder, enriched with component metadata.

    Example:
        .. code-block:: python

            from pathlib import Path
            import dagster as dg

            @dg.definitions
            def defs():
                project_path = Path("/path/to/my/dg/project")
                return dg.load_from_defs_folder(project_root=project_path)

    """
    root_config_path = locate_dg_config_in_folder(project_root)
    toml_config = load_toml_as_dict(
        check.not_none(
            root_config_path,
            additional_message=f"No config file found at project root {project_root}",
        )
    )

    if root_config_path and root_config_path.stem == "dg":
        project = toml_config.get("project", {})
    else:
        project = toml_config.get("tool", {}).get("dg", {}).get("project", {})

    root_module_name = project.get("root_module")
    defs_module_name = project.get("defs_module")
    check.invariant(
        defs_module_name or root_module_name,
        f"Either defs_module or root_module must be set in the project config {root_config_path}",
    )
    defs_module_name = get_canonical_defs_module_name(defs_module_name, root_module_name)

    defs_module = importlib.import_module(defs_module_name)

    return load_defs(
        defs_module, project_root=project_root, terminate_autoloading_on_keyword_files=False
    )


# Public method so optional Nones are fine
@deprecated(
    breaking_version="1.11",
    additional_warn_text="Use load_from_defs_folder instead.",
)
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
    project_root = project_root if project_root else get_project_root(defs_root)

    tree = (
        LegacyAutoloadingComponentTree.from_module(defs_module=defs_root, project_root=project_root)
        if terminate_autoloading_on_keyword_files
        else ComponentTree.from_module(defs_module=defs_root, project_root=project_root)
    )

    return tree.build_defs()


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
