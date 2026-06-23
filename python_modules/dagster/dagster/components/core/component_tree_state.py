import warnings
from collections import defaultdict
from pathlib import Path

from dagster_shared.record import record, replace
from typing_extensions import TypeVar

from dagster._core.definitions.definitions_class import Definitions
from dagster.components.component.component import Component
from dagster.components.core.context import ComponentDeclLoadContext, ComponentLoadContext
from dagster.components.core.decl import ComponentDecl
from dagster.components.core.defs_module import (
    ComponentLoc,
    ComponentPath,
    ResolvableToComponentLoc,
    ResolvableToComponentPath,
)

PLUGIN_COMPONENT_TYPES_JSON_METADATA_KEY = "plugin_component_types_json"

T = TypeVar("T", bound=Component)


class ComponentTreeException(Exception):
    pass


class DuplicateDefsStateKeyWarning(Warning):
    """Warning raised when multiple StateBackedComponents share the same defs state key."""

    pass


@record
class _CacheData:
    """Data that is cached for a given component location."""

    defs: Definitions | None = None
    component: Component | None = None
    load_context: ComponentLoadContext | None = None
    component_decl: ComponentDecl | None = None
    decl_load_context: ComponentDeclLoadContext | None = None


class ComponentTreeStateTracker:
    """Stateful class which tracks the state of the component tree
    as it is loaded.
    """

    def __init__(self, defs_module_path: Path):
        self._defs_module_path = defs_module_path
        self._component_load_dependents_dict: dict[ComponentLoc, set[ComponentLoc]] = defaultdict(
            set
        )
        self._component_defs_dependents_dict: dict[ComponentLoc, set[ComponentLoc]] = defaultdict(
            set
        )
        self._component_defs_state_key_dict: dict[str, ComponentLoc] = {}
        self._cache: dict[ComponentLoc, _CacheData] = defaultdict(_CacheData)

    def _resolve_loc(self, loc: ResolvableToComponentLoc) -> ComponentLoc:
        """Resolve a loc-like value to a ComponentLoc."""
        if isinstance(loc, ComponentLoc):
            return loc
        # Fall back to ComponentPath resolution for Path/str
        return ComponentPath.from_resolvable(self._defs_module_path, loc)

    def _invalidate_loc_inner(self, loc: ComponentLoc, visited: set[ComponentLoc]) -> None:
        """Invalidate the cache for a given component loc and all of its dependents."""
        # Invalidate both the fully-specified loc and the generic loc (without an instance key)
        # because some cache data (e.g. component decl information) is stored on the generic loc
        # before the instance key is known.
        for p in {loc, loc.without_instance_key()}:
            if p in visited:
                continue
            self._cache.pop(p, None)
            visited.add(p)
            deps = self.get_direct_defs_dependents(p) | self.get_direct_load_dependents(p)
            for d in deps:
                if d not in visited:
                    self._invalidate_loc_inner(d, visited)

    def invalidate_loc(self, loc: ResolvableToComponentLoc) -> None:
        """Invalidates the cache for a given component loc and all of its dependents."""
        resolved = self._resolve_loc(loc)
        self._invalidate_loc_inner(resolved, set())

    def invalidate_path(self, path: ResolvableToComponentPath) -> None:
        """Invalidates the cache for a given component path and all of its dependents.

        Convenience method that delegates to invalidate_loc.
        """
        self.invalidate_loc(path)

    def invalidate_by_defs_state_key(self, defs_state_key: str) -> None:
        """Invalidates the cache for the component associated with the given defs state key,
        cascading to all dependents.

        This is the primary mechanism for hot-reload: when external state changes
        (e.g. app-managed components or state-backed component data), the caller invalidates
        by state key and the dependency graph ensures all affected components rebuild.
        """
        loc = self._component_defs_state_key_dict.get(defs_state_key)
        if loc is not None:
            self.invalidate_loc(loc)

    def get_cache_data(self, loc: ResolvableToComponentLoc) -> _CacheData:
        resolved = self._resolve_loc(loc)
        return self._cache[resolved]

    def set_cache_data(self, loc: ResolvableToComponentLoc, **kwargs) -> None:
        resolved = self._resolve_loc(loc)
        current_data = self._cache[resolved]
        self._cache[resolved] = replace(current_data, **kwargs)

    def mark_component_load_dependency(self, from_loc: ComponentLoc, to_loc: ComponentLoc) -> None:
        self._component_load_dependents_dict[to_loc].add(from_loc)

    def mark_component_defs_dependency(self, from_loc: ComponentLoc, to_loc: ComponentLoc) -> None:
        self._component_defs_dependents_dict[to_loc].add(from_loc)

    def mark_component_defs_state_key(self, loc: ComponentLoc, defs_state_key: str) -> None:
        # warns if components share the same defs state key
        existing_loc = self._component_defs_state_key_dict.get(defs_state_key)
        if existing_loc is not None and existing_loc != loc:
            warnings.warn(
                f"Multiple components have the same defs state key: {defs_state_key}\n"
                "Component locs: \n"
                f"  {existing_loc}\n"
                f"  {loc}\n"
                "Configure or override the `get_defs_state_config` method on one or both components to disambiguate.",
                category=DuplicateDefsStateKeyWarning,
                stacklevel=2,
            )
        self._component_defs_state_key_dict[defs_state_key] = loc

    def get_direct_load_dependents(self, loc: ComponentLoc) -> set[ComponentLoc]:
        """Returns the set of components that directly depend on the given component.

        Args:
            loc: The loc of the component to get the direct load dependents of.
        """
        return self._component_load_dependents_dict[loc]

    def get_direct_defs_dependents(self, loc: ComponentLoc) -> set[ComponentLoc]:
        """Returns the set of components that directly depend on the given component's defs.

        Args:
            loc: The loc of the component to get the direct defs dependents of.
        """
        return self._component_defs_dependents_dict[loc]
