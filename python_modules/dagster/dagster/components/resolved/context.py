import os
import sys
import traceback
from collections.abc import Mapping, Sequence
from typing import Any, Optional, TypeVar, Union, overload

from dagster_shared.yaml_utils.source_position import SourcePositionTree
from jinja2 import Undefined
from jinja2.exceptions import UndefinedError
from jinja2.nativetypes import NativeTemplate
from pydantic import BaseModel

from dagster._core.definitions.declarative_automation.automation_condition import (
    AutomationCondition,
)
from dagster._record import copy, record
from dagster.components.resolved.errors import ResolutionException

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
    path: list[Union[str, int]] = []
    source_position_tree: Optional[SourcePositionTree] = None

    def at_path(self, path_part: Union[str, int]):
        return copy(self, path=[*self.path, path_part])

    @staticmethod
    def default(source_position_tree: Optional[SourcePositionTree] = None) -> "ResolutionContext":
        return ResolutionContext(
            scope={"env": env_scope, "automation_condition": automation_condition_scope()},
            source_position_tree=source_position_tree,
        )

    def with_scope(self, **additional_scope) -> "ResolutionContext":
        return copy(self, scope={**self.scope, **additional_scope})

    def with_source_position_tree(
        self, source_position_tree: SourcePositionTree
    ) -> "ResolutionContext":
        return copy(self, source_position_tree=source_position_tree)

    def _location_parts(self, inline_err: str) -> list[str]:
        if not self.source_position_tree:
            return []

        source = self.source_position_tree.source_error(
            yaml_path=self.path,
            inline_error_message=inline_err,
            value_error=True,
        )
        return [
            f"{source.file_name}:{source.start_line_no} - {source.location}\n{source.snippet}\n",
        ]

    def _invalid_scope_exc(self, undefined_message: str) -> ResolutionException:
        msg_parts = self._location_parts(undefined_message)
        idx = undefined_message.find(" is undefined")
        if idx > 0:
            missing_scope = undefined_message[:idx]
            msg_parts.append(
                f"UndefinedError: {missing_scope} not found in scope, available scope is: {', '.join(self.scope.keys())}\n"
            )
        else:
            msg_parts.append(f"UndefinedError: {undefined_message}\n")

        return ResolutionException("".join(msg_parts))

    def _scope_threw_exc(self, fmt_exc: list[str]):
        msg_parts = self._location_parts(fmt_exc[-1] if fmt_exc else "ResolutionException")
        msg_parts.append("Exception occurred while evaluating template.\n")
        # strip the system frames from the stack trace
        template_seen = False
        for line in fmt_exc:
            if "in top-level template code" in line:
                template_seen = True
            if line.strip().startswith("File") and not template_seen:
                continue
            msg_parts.append(line)

        return ResolutionException("".join(msg_parts))

    def build_resolve_fn_exc(
        self,
        fmt_exc: list[str],
        field_name: str,
        model: BaseModel,
    ) -> ResolutionException:
        msg_parts = self._location_parts(fmt_exc[-1] if fmt_exc else "ResolutionException")
        msg_parts.append(
            f"Exception occurred in Resolver for field '{field_name}' resolving from {model.__class__.__name__}.\n"
        )
        msg_parts.extend(fmt_exc)

        return ResolutionException("".join(msg_parts))

    def _resolve_inner_value(self, val: Any) -> Any:
        """Resolves a single value, if it is a templated string."""
        if isinstance(val, str):
            try:
                val = NativeTemplate(val).render(**self.scope)
                if isinstance(val, Undefined):
                    raise self._invalid_scope_exc(val._undefined_message) from None  # noqa: SLF001
                return val
            except UndefinedError as undefined_error:
                if undefined_error.message:
                    raise self._invalid_scope_exc(undefined_error.message) from None
                else:
                    raise
            except Exception as e:
                if not isinstance(e, ResolutionException):
                    fmt_exc = traceback.format_exception(*sys.exc_info())
                    raise self._scope_threw_exc(fmt_exc) from None
                else:
                    raise
        else:
            return val

    @overload
    def resolve_value(self, val: Any, as_type: type[T]) -> T: ...

    @overload
    def resolve_value(self, val: Mapping) -> Mapping: ...

    @overload
    def resolve_value(self, val: tuple) -> tuple: ...

    @overload
    def resolve_value(self, val: Sequence) -> Sequence: ...

    def resolve_value(self, val: Any, as_type: Optional[type] = None) -> Any:
        """Recursively resolves templated values in a nested object."""
        if isinstance(val, dict):
            return {k: self.at_path(k).resolve_value(v) for k, v in val.items()}
        elif isinstance(val, tuple):
            return tuple(self.at_path(i).resolve_value(v) for i, v in enumerate(val))
        elif isinstance(val, list):
            return [self.at_path(i).resolve_value(v) for i, v in enumerate(val)]
        else:
            return self._resolve_inner_value(val)
