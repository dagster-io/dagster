import importlib
from pathlib import Path
from types import ModuleType

from dagster_shared.serdes.objects.package_entry import json_for_all_components

from dagster._annotations import deprecated
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

    return load_defs(defs_root=defs_root)


# Public method so optional Nones are fine
@suppress_dagster_warnings
def load_defs(defs_root: ModuleType) -> Definitions:
    """Constructs a Definitions object, loading all Dagster defs in the given module.

    Args:
        defs_root (Path): The path to the defs root, typically `package.defs`.
        resources (Optional[Mapping[str, object]]): A mapping of resource keys to resources
            to apply to the definitions.
    """
    from dagster.components.core.defs_module import get_component
    from dagster.components.core.package_entry import discover_entry_point_package_objects
    from dagster.components.core.snapshot import get_package_entry_snap

    # create a top-level DefsModule component from the root module
    context = ComponentLoadContext.for_module(defs_root)
    root_component = get_component(context)
    if root_component is None:
        raise DagsterInvalidDefinitionError("Could not resolve root module to a component.")

    library_objects = discover_entry_point_package_objects()
    snaps = [get_package_entry_snap(key, obj) for key, obj in library_objects.items()]
    components_json = json_for_all_components(snaps)

    with use_component_load_context(context):
        return Definitions.merge(
            root_component.build_defs(context),
            Definitions(metadata={PLUGIN_COMPONENT_TYPES_JSON_METADATA_KEY: components_json}),
        )
