"""Generic type resolver registry for mapping typing generics to DagsterTypes.

This module provides a pluggable system for resolving generic typing annotations
(e.g., list[int], Optional[str]) to Dagster types. It supports:

  - Explicit registration via register_generic_type_resolver()
  - Automatic discovery via entrypoints in the 'dagster.generic_resolvers' group
  - Opt-in hooks via __dagster_generic_resolver__ attribute on types

Libraries can integrate by registering a resolver function that transforms
generic type arguments into DagsterType objects, allowing Dagster core to
remain library-agnostic while supporting custom generics from any installed package.
"""

from __future__ import annotations

import typing as t
from importlib import metadata

import dagster._check as check
from dagster._core.errors import DagsterInvalidDefinitionError
from dagster._core.types.dagster_type import DagsterType
from dagster._utils.typing_api import get_args, get_origin

# A resolver transforms generic type arguments into a DagsterType.
GenericResolver = t.Callable[[t.Tuple[t.Any, ...]], DagsterType]

_GENERIC_RESOLVERS: dict[object, GenericResolver] = {}
_ENTRYPOINT_GROUP = "dagster.generic_resolvers"
_ENTRYPOINTS_LOADED = False


def _get_resolver_for_origin(origin: object) -> t.Optional[GenericResolver]:
    """Lookup a resolver from the registry or an origin-defined hook.
    
    First checks the explicit registry, then falls back to a __dagster_generic_resolver__
    attribute on the origin itself.
    
    Args:
        origin: The generic origin (e.g., list, dict, custom generic).
    
    Returns:
        A GenericResolver if found, None otherwise.
    """

    resolver = _GENERIC_RESOLVERS.get(origin)
    if resolver is not None:
        return resolver

    attr_resolver = getattr(origin, "__dagster_generic_resolver__", None)
    if attr_resolver is None:
        return None

    check.callable_param(attr_resolver, "__dagster_generic_resolver__")
    return t.cast(GenericResolver, attr_resolver)


def _fetch_entrypoints() -> t.Any:
    """Fetch all entry points, raising a clear error if it fails."""
    try:
        return metadata.entry_points()
    except Exception as exc:  # pragma: no cover
        raise DagsterInvalidDefinitionError(
            "Failed to load Dagster generic resolver entrypoints"
        ) from exc


def _select_entrypoint_group(eps: t.Any) -> t.Iterable[metadata.EntryPoint]:
    """Select entry points for the generic resolver group, supporting both old and new APIs."""
    # Newer importlib versions (3.10+) use .select(); fallback to dict-like .get()
    if hasattr(eps, "select"):
        return eps.select(group=_ENTRYPOINT_GROUP)
    else:
        return eps.get(_ENTRYPOINT_GROUP, [])


def _execute_entrypoint_hooks(group: t.Iterable[metadata.EntryPoint]) -> None:
    """Load and execute each entrypoint hook in the group."""
    for ep in group:
        try:
            fn = ep.load()
            check.callable_param(fn, ep.name)
            fn()
        except Exception as exc:  # pragma: no cover
            raise DagsterInvalidDefinitionError(
                f"Error while loading generic resolver entrypoint '{ep.name}'"
            ) from exc


def register_generic_type_resolver(origin: object, resolver: GenericResolver) -> None:
    """Register a resolver for typing constructs with the given origin.
    
    This allows external libraries to teach Dagster how to resolve their custom generics.
    Each origin can only be registered once; attempting to register a different resolver
    for the same origin raises an error.
    
    Typically called from an entrypoint hook in the 'dagster.generic_resolvers' group.
    
    Args:
        origin: The generic origin to register (e.g., list, custom generic class).
        resolver: A callable that transforms type arguments into a DagsterType.
    
    Raises:
        DagsterInvalidDefinitionError: If a different resolver is already registered.
    """

    check.not_none_param(origin, "origin")
    check.callable_param(resolver, "resolver")

    existing = _GENERIC_RESOLVERS.get(origin)
    if existing is not None and existing is not resolver:
        raise DagsterInvalidDefinitionError(
            "A generic resolver has already been registered for origin "
            f"{origin!r}. Generic resolvers can only be registered once per origin."
        )

    _GENERIC_RESOLVERS[origin] = resolver


def _load_entrypoint_resolvers() -> None:
    """Load resolver registration hooks advertised via entrypoints.

    Integrations can declare an entry in the ``dagster.generic_resolvers`` group pointing to a
    callable that registers one or more resolvers (typically by calling
    ``register_generic_type_resolver``). This loads once, lazily at first resolution.
    
    Raises:
        DagsterInvalidDefinitionError: If loading or executing entrypoint hooks fails.
    """

    global _ENTRYPOINTS_LOADED
    if _ENTRYPOINTS_LOADED:
        return

    _ENTRYPOINTS_LOADED = True
    
    eps = _fetch_entrypoints()
    group = _select_entrypoint_group(eps)
    _execute_entrypoint_hooks(group)


def try_resolve_generic(typing_type: object) -> t.Optional[DagsterType]:
    """Attempt to resolve a typing annotation using the generic resolver registry.
    
    This is the primary entry point for resolving generic typing annotations to DagsterTypes.
    It:
    1. Loads any entrypoint-based resolvers (lazily, on first call).
    2. Extracts the origin from the typing annotation.
    3. Looks up a resolver for that origin.
    4. Invokes the resolver with the type arguments.
    
    Args:
        typing_type: A typing annotation, possibly generic (e.g., list[int], MyGeneric[T]).
    
    Returns:
        A DagsterType if a resolver is found and succeeds, None otherwise.
    """

    _load_entrypoint_resolvers()

    origin = get_origin(typing_type)
    if origin is None:
        return None

    resolver = _get_resolver_for_origin(origin)
    if resolver is None:
        return None

    args = get_args(typing_type)
    return resolver(args)
