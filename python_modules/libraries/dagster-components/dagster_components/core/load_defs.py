import importlib
from collections.abc import Mapping
from dataclasses import dataclass
from pathlib import Path
from types import ModuleType
from typing import Optional

from dagster import Definitions
from dagster._annotations import deprecated
from dagster._utils.cached_method import cached_method
from dagster._utils.warnings import suppress_dagster_warnings

from dagster_components.core.context import ComponentLoadContext, use_component_load_context
from dagster_components.resolved.context import ResolutionContext
from dagster_components.utils import get_path_from_module


@dataclass
class DefinitionsModuleCache:
    """Cache used when loading a code location's component hierarchy.
    Stores resources and a cache to ensure we don't load the same component multiple times.
    """

    resources: Mapping[str, object]

    def load_defs(self, module: ModuleType) -> Definitions:
        """Loads a set of Dagster definitions from a components Python module.

        Args:
            module (ModuleType): The Python module to load definitions from.

        Returns:
            Definitions: The set of Dagster definitions loaded from the module.
        """
        return self._load_defs_inner(module)

    @cached_method
    def _load_defs_inner(self, module: ModuleType) -> Definitions:
        from dagster_components.core.defs_module import DefsModuleDecl

        decl_node = DefsModuleDecl.from_module(module)
        if not decl_node:
            raise Exception(f"No component found at module {module}")

        context = ComponentLoadContext(
            defs_root=get_path_from_module(module),
            defs_module_name=module.__name__,
            decl_node=decl_node,
            resolution_context=ResolutionContext.default(
                source_position_tree=decl_node.get_source_position_tree()
            ),
            module_cache=self,
        )
        defs_module = decl_node.load(context)
        with use_component_load_context(context):
            return defs_module.build_defs()


@deprecated(breaking_version="0.2.0")
@suppress_dagster_warnings
def build_component_defs(
    components_root: Path, resources: Optional[Mapping[str, object]] = None
) -> Definitions:
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
) -> Definitions:
    """Constructs a Definitions object, loading all Dagster defs in the given module.

    Args:
        defs_root (Path): The path to the defs root, typically `package.defs`.
        resources (Optional[Mapping[str, object]]): A mapping of resource keys to resources
            to apply to the definitions.
    """
    module_cache = DefinitionsModuleCache(resources=resources or {})
    return module_cache.load_defs(defs_root)
