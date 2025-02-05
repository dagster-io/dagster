import os
from collections.abc import Mapping
from typing import Any, Optional

from dagster._core.definitions.declarative_automation.automation_condition import (
    AutomationCondition,
)
from dagster._record import record
from jinja2.nativetypes import NativeTemplate

from dagster_components.core.schema.base import ResolvableModel


def env_scope(key: str) -> Optional[str]:
    return os.environ.get(key)


def automation_condition_scope() -> Mapping[str, Any]:
    return {
        "eager": AutomationCondition.eager,
        "on_cron": AutomationCondition.on_cron,
    }


@record
class ResolveContext:
    scope: Mapping[str, Any]

    @staticmethod
    def default() -> "ResolveContext":
        return ResolveContext(
            scope={"env": env_scope, "automation_condition": automation_condition_scope()}
        )

    def with_scope(self, **additional_scope) -> "ResolveContext":
        return ResolveContext(scope={**self.scope, **additional_scope})

    def _resolve_inner_value(self, val: Any) -> Any:
        """Resolves a single value, if it is a templated string."""
        return NativeTemplate(val).render(**self.scope) if isinstance(val, str) else val

    def resolve_value(self, val: Any) -> Any:
        """Recursively resolves templated values in a nested object."""
        if isinstance(val, ResolvableModel):
            return val.resolve(self)
        elif isinstance(val, dict):
            return {k: self.resolve_value(v) for k, v in val.items()}
        elif isinstance(val, list):
            return [self.resolve_value(v) for v in val]
        else:
            return self._resolve_inner_value(val)
