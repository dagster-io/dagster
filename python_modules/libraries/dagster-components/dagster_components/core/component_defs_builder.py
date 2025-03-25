import importlib
from collections.abc import Mapping, Sequence
from pathlib import Path
from types import ModuleType
from typing import TYPE_CHECKING, Optional

from dagster import Definitions
from dagster._annotations import deprecated
from dagster._utils.warnings import suppress_dagster_warnings

from dagster_components.core.component import (
    Component,
    ComponentLoadContext,
    DefinitionsModuleCache,
)

if TYPE_CHECKING:
    from dagster import Definitions


@suppress_dagster_warnings
def defs_from_components(
    *,
    context: ComponentLoadContext,
    components: Sequence[Component],
    resources: Mapping[str, object],
) -> "Definitions":
    from dagster._core.definitions.definitions_class import Definitions

    return Definitions.merge(
        *[
            *[
                c.build_defs(context.with_rendering_scope(c.get_additional_scope()))
                for c in components
            ],
            Definitions(resources=resources),
        ]
    )


@deprecated(breaking_version="0.2.0")
@suppress_dagster_warnings
def build_component_defs(
    components_root: Path, resources: Optional[Mapping[str, object]] = None
) -> "Definitions":
    """Build a Definitions object for all the component instances in a given code location.

    Args:
        components_root (Path): The path to the components root. This is a directory containing
            subdirectories with component instances.
    """
    defs_root = importlib.import_module(
        f"{Path(components_root).parent.name}.{Path(components_root).name}"
    )

    return load_defs(defs_root=defs_root, resources=resources)


# Public method so optional Nones are fine
@suppress_dagster_warnings
def load_defs(
    defs_root: ModuleType, resources: Optional[Mapping[str, object]] = None
) -> "Definitions":
    """Constructs a Definitions object, loading all Dagster defs in the given module.

    Args:
        defs_root (Path): The path to the defs root, typically `package.defs`.
        resources (Optional[Mapping[str, object]]): A mapping of resource keys to resources
            to apply to the definitions.
    """
    module_cache = DefinitionsModuleCache(resources=resources or {})
    return module_cache.load_defs(defs_root)
