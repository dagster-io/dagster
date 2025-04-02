import importlib
from pathlib import Path
from types import ModuleType

from dagster._annotations import deprecated
from dagster._core.definitions.definitions_class import Definitions
from dagster._core.errors import DagsterInvalidDefinitionError
from dagster._utils.warnings import suppress_dagster_warnings
from dagster.components.core.context import ComponentLoadContext, use_component_load_context


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
    from dagster.components.core.defs_module import DefsModuleComponent

    # create a top-level DefsModule component from the root module
    context = ComponentLoadContext.for_module(defs_root)
    root_component = DefsModuleComponent.from_context(context)
    if root_component is None:
        raise DagsterInvalidDefinitionError("Could not resolve root module to a component.")

    with use_component_load_context(context):
        return root_component.build_defs(context)
