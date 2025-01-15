import functools
import os
import re
from collections.abc import Mapping, Sequence
from typing import Any, Callable, Optional, TypeVar, Union

from dagster._core.definitions.declarative_automation.automation_condition import (
    AutomationCondition,
)
from dagster._record import record
from dagster._utils.pydantic_yaml import YamlConvertableToValidationError
from jinja2 import UndefinedError
from jinja2.nativetypes import NativeTemplate
from pydantic import BaseModel

from dagster_components.core.schema.metadata import allow_render

UNDEFINED_MSG_REGEX = re.compile(r"'(.+)' is undefined")

T = TypeVar("T")


def env_scope(key: str) -> Optional[str]:
    return os.environ.get(key)


def automation_condition_scope() -> Mapping[str, Any]:
    return {
        "eager": AutomationCondition.eager,
        "on_cron": AutomationCondition.on_cron,
    }


ShouldResolveFn = Callable[[Sequence[Union[str, int]]], bool]


@record
class TemplatedValueResolver:
    context: Mapping[str, Any]

    @staticmethod
    def default() -> "TemplatedValueResolver":
        return TemplatedValueResolver(
            context={"env": env_scope, "automation_condition": automation_condition_scope()}
        )

    def with_context(self, **additional_context) -> "TemplatedValueResolver":
        return TemplatedValueResolver(context={**self.context, **additional_context})

    def _render_value(self, val: Any) -> Any:
        """Resolves a single value, if it is a templated string."""
        return NativeTemplate(val).render(**self.context) if isinstance(val, str) else val

    def _render_obj(
        self,
        obj: Any,
        valpath: Optional[Sequence[Union[str, int]]],
        should_render: Callable[[Sequence[Union[str, int]]], bool],
    ) -> Any:
        """Recursively renders templated values in a nested object, based on the provided should_render function."""
        if valpath is not None and not should_render(valpath):
            return obj
        elif isinstance(obj, dict):
            # render all values in the dict
            return {
                k: self._render_obj(
                    v, [*valpath, k] if valpath is not None else None, should_render
                )
                for k, v in obj.items()
            }
        elif isinstance(obj, list):
            # render all values in the list
            return [
                self._render_obj(v, [*valpath, i] if valpath is not None else None, should_render)
                for i, v in enumerate(obj)
            ]
        else:
            try:
                return self._render_value(obj)

            except UndefinedError as e:
                undefined_value = UNDEFINED_MSG_REGEX.match(e.message or "")
                available_scopes = ", ".join(self.context.keys())
                message = (
                    (
                        f"Error rendering value: `{undefined_value.group(1)}` not found in scope, "
                        f"available scope is: {available_scopes}"
                    )
                    if undefined_value
                    else e.message or "Unknown scope"
                )

                raise YamlConvertableToValidationError(
                    message=message, path=tuple(valpath) if valpath else tuple()
                ) from None

    def render_obj(self, val: Any) -> Any:
        """Recursively renders templated values in a nested object."""
        return self._render_obj(val, None, lambda _: True)

    def render_params(self, val: T, target_type: type) -> T:
        """Given a raw params value, preprocesses it by rendering any templated values that are not marked as deferred in the target_type's json schema."""
        json_schema = (
            target_type.model_json_schema() if issubclass(target_type, BaseModel) else None
        )
        if json_schema is None:
            should_render = lambda _: True
        else:
            should_render = functools.partial(
                allow_render, json_schema=json_schema, subschema=json_schema
            )
        return self._render_obj(val, [], should_render=should_render)
