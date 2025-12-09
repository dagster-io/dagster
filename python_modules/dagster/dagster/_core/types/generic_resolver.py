from __future__ import annotations

import typing as t
from importlib import metadata

import dagster._check as check
from dagster._core.errors import DagsterInvalidDefinitionError
from dagster._core.types.dagster_type import DagsterType
from dagster._utils.typing_api import get_args, get_origin

GenericResolver = t.Callable[[t.Tuple[t.Any, ...]], DagsterType]

_GENERIC_RESOLVERS: dict[object, GenericResolver] = {}
_ENTRYPOINT_GROUP = "dagster.generic_resolvers"
_ENTRYPOINTS_LOADED = False


def _get_resolver_for_origin(origin: object) -> t.Optional[GenericResolver]:
    """Lookup a resolver from the registry or an origin-defined hook."""

    resolver = _GENERIC_RESOLVERS.get(origin)
    if resolver is not None:
        return resolver

    attr_resolver = getattr(origin, "__dagster_generic_resolver__", None)
    if attr_resolver is None:
        return None

    check.callable_param(attr_resolver, "__dagster_generic_resolver__")
    return attr_resolver  # type: ignore[return-value]


def register_generic_type_resolver(origin: object, resolver: GenericResolver) -> None:
    """Register a resolver for typing constructs with the given origin."""

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

    Example ``pyproject.toml`` entry:

    [project.entry-points."dagster.generic_resolvers"]
    my_integration = "my_package.resolvers:register_resolvers"

    Where ``register_resolvers`` is a callable that invokes ``register_generic_type_resolver`` for
    any supported generic origins.
    """

    global _ENTRYPOINTS_LOADED
    if _ENTRYPOINTS_LOADED:
        return

    _ENTRYPOINTS_LOADED = True
    try:
        eps = metadata.entry_points()
    except Exception as exc:  # pragma: no cover
        raise DagsterInvalidDefinitionError(
            "Failed to load Dagster generic resolver entrypoints"
        ) from exc

    group = eps.select(group=_ENTRYPOINT_GROUP) if hasattr(eps, "select") else eps.get(
        _ENTRYPOINT_GROUP, []
    )

    for ep in group:
        try:
            fn = ep.load()
            check.callable_param(fn, ep.name)
            fn()
        except Exception as exc:  # pragma: no cover
            raise DagsterInvalidDefinitionError(
                f"Error while loading generic resolver entrypoint '{ep.name}'"
            ) from exc


def try_resolve_generic(typing_type: object) -> t.Optional[DagsterType]:
    """Attempt to resolve a typing annotation using the generic resolver registry."""

    _load_entrypoint_resolvers()

    origin = get_origin(typing_type)
    if origin is None:
        return None

    resolver = _get_resolver_for_origin(origin)
    if resolver is None:
        return None

    args = get_args(typing_type)
    return resolver(args)
