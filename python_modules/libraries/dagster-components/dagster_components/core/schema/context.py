import os
from collections.abc import Mapping, Sequence
from typing import Any, Optional, TypeVar, overload

from dagster._core.definitions.declarative_automation.automation_condition import (
    AutomationCondition,
)
from dagster._record import record
from jinja2.nativetypes import NativeTemplate

from dagster_components.core.schema.base import ResolvableModel

T = TypeVar("T")


def env_scope(key: str) -> Optional[str]:
    return os.environ.get(key)


def automation_condition_scope() -> Mapping[str, Any]:
    return {
        "eager": AutomationCondition.eager,
        "on_cron": AutomationCondition.on_cron,
    }


T = TypeVar("T")


@record
class ResolutionContext:
    scope: Mapping[str, Any]

    @staticmethod
    def default() -> "ResolutionContext":
        return ResolutionContext(
            scope={"env": env_scope, "automation_condition": automation_condition_scope()}
        )

    def with_scope(self, **additional_scope) -> "ResolutionContext":
        return ResolutionContext(scope={**self.scope, **additional_scope})

    def _resolve_inner_value(self, val: Any) -> Any:
        """Resolves a single value, if it is a templated string."""
        if isinstance(val, ResolvableModel):
            resolver = val.__dagster_resolver__(val)
            return resolver.resolve(self)
        elif isinstance(val, str):
            return NativeTemplate(val).render(**self.scope)
        else:
            return val

    @overload
    def resolve_value(self, val: str) -> Any: ...

    @overload
    def resolve_value(self, val: Mapping) -> Mapping: ...

    @overload
    def resolve_value(self, val: tuple) -> tuple: ...

    @overload
    def resolve_value(self, val: Sequence) -> Sequence: ...

    @overload
    def resolve_value(self, val: Optional[str]) -> Optional[Any]: ...

    @overload
    def resolve_value(self, val: Optional[Mapping]) -> Optional[Mapping]: ...

    @overload
    def resolve_value(self, val: Optional[tuple]) -> Optional[tuple]: ...

    @overload
    def resolve_value(self, val: Optional[Sequence]) -> Optional[Sequence]: ...

    @overload
    def resolve_value(self, val: Any) -> Any: ...

    def resolve_value(self, val: Any) -> Any:
        """Recursively resolves templated values in a nested object."""
        if isinstance(val, dict):
            return {k: self.resolve_value(v) for k, v in val.items()}
        elif isinstance(val, tuple):
            return tuple(self.resolve_value(v) for v in val)
        elif isinstance(val, list):
            return [self.resolve_value(v) for v in val]
        else:
            return self._resolve_inner_value(val)
