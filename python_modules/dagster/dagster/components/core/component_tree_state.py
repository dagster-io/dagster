from collections import defaultdict
from pathlib import Path
from typing import Optional

from dagster_shared.record import record, replace
from typing_extensions import TypeVar

from dagster._core.definitions.definitions_class import Definitions
from dagster._core.errors import DagsterInvalidDefinitionError
from dagster.components.component.component import Component
from dagster.components.core.context import ComponentDeclLoadContext, ComponentLoadContext
from dagster.components.core.decl import ComponentDecl
from dagster.components.core.defs_module import ComponentPath, ResolvableToComponentPath

PLUGIN_COMPONENT_TYPES_JSON_METADATA_KEY = "plugin_component_types_json"

T = TypeVar("T", bound=Component)


class ComponentTreeException(Exception):
    pass


@record
class _CacheData:
    """Data that is cached for a given component path."""

    defs: Optional[Definitions] = None
    component: Optional[Component] = None
    load_context: Optional[ComponentLoadContext] = None
    component_decl: Optional[ComponentDecl] = None
    decl_load_context: Optional[ComponentDeclLoadContext] = None


class ComponentTreeStateTracker:
    """Stateful class which tracks the state of the component tree
    as it is loaded.
    """

    def __init__(self, defs_module_path: Path):
        self._defs_module_path = defs_module_path
        self._component_load_dependents_dict: dict[ComponentPath, set[ComponentPath]] = defaultdict(
            set
        )
        self._component_defs_dependents_dict: dict[ComponentPath, set[ComponentPath]] = defaultdict(
            set
        )
        self._component_defs_state_key_dict: dict[str, ComponentPath] = {}
        self._cache: dict[ComponentPath, _CacheData] = defaultdict(_CacheData)

    def _invalidate_path_inner(self, path: ComponentPath, visited: set[ComponentPath]) -> None:
        """Invalidate the cache for a given component path and all of its dependents."""
        # we invalidate both the fully-specified path and the generic path (without an instance key)
        # because some cache data (e.g. component decl information) is stored on the generic path
        # because it is generated before we know the instance key
        for p in [path, path.without_instance_key()]:
            self._cache.pop(p, None)
            visited.add(p)
            deps = self.get_direct_defs_dependents(p) | self.get_direct_load_dependents(p)
            for d in deps:
                if d not in visited:
                    self._invalidate_path_inner(d, visited)

    def invalidate_path(self, path: ResolvableToComponentPath) -> None:
        """Invalidates the cache for a given component path and all of its dependents."""
        path = ComponentPath.from_resolvable(self._defs_module_path, path)
        self._invalidate_path_inner(path, set())

    def get_cache_data(self, path: ResolvableToComponentPath) -> _CacheData:
        resolved_path = ComponentPath.from_resolvable(self._defs_module_path, path)
        return self._cache[resolved_path]

    def set_cache_data(self, path: ResolvableToComponentPath, **kwargs) -> None:
        resolved_path = ComponentPath.from_resolvable(self._defs_module_path, path)
        current_data = self._cache[resolved_path]
        self._cache[resolved_path] = replace(current_data, **kwargs)

    def mark_component_load_dependency(
        self, from_path: ComponentPath, to_path: ComponentPath
    ) -> None:
        self._component_load_dependents_dict[to_path].add(from_path)

    def mark_component_defs_dependency(
        self, from_path: ComponentPath, to_path: ComponentPath
    ) -> None:
        self._component_defs_dependents_dict[to_path].add(from_path)

    def mark_component_defs_state_key(self, path: ComponentPath, defs_state_key: str) -> None:
        # ensures that no components share the same defs state key
        existing_path = self._component_defs_state_key_dict.get(defs_state_key)
        if existing_path is not None and existing_path != path:
            raise DagsterInvalidDefinitionError(
                f"Multiple components have the same defs state key: {defs_state_key}\n"
                "Component paths: \n"
                f"  {existing_path}\n"
                f"  {path}\n"
                "Configure or override the `get_defs_state_key` method on one or both components to disambiguate."
            )
        self._component_defs_state_key_dict[defs_state_key] = path

    def get_direct_load_dependents(self, path: ComponentPath) -> set[ComponentPath]:
        """Returns the set of components that directly depend on the given component.

        Args:
            path: The path to the component to get the direct load dependents of.
        """
        return self._component_load_dependents_dict[path]

    def get_direct_defs_dependents(self, path: ComponentPath) -> set[ComponentPath]:
        """Returns the set of components that directly depend on the given component's defs.

        Args:
            defs_module_path: The path to the defs module.
            component_path: The path to the component to get the direct defs dependents of.
        """
        return self._component_defs_dependents_dict[path]
