from __future__ import annotations

import typing as t

import dagster._check as check
from dagster._core.errors import DagsterInvalidDefinitionError
from dagster._core.types.dagster_type import DagsterType
from dagster._utils.typing_api import get_args, get_origin

GenericResolver = t.Callable[[t.Tuple[t.Any, ...]], DagsterType]

_GENERIC_RESOLVERS: dict[object, GenericResolver] = {}


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


def try_resolve_generic(typing_type: object) -> t.Optional[DagsterType]:
    """Attempt to resolve a typing annotation using the generic resolver registry."""

    origin = get_origin(typing_type)
    if origin is None:
        return None

    resolver = _GENERIC_RESOLVERS.get(origin)
    if resolver is None:
        return None

    args = get_args(typing_type)
    return resolver(args)
