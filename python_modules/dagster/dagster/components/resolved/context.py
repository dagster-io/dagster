import os
import sys
import traceback
from collections.abc import Mapping, Sequence
from pathlib import Path
from typing import Any, Optional, TypeVar, Union, overload

from dagster_shared.yaml_utils.source_position import SourcePositionTree
from pydantic import BaseModel

from dagster._annotations import public
from dagster._core.definitions.declarative_automation.automation_condition import (
    AutomationCondition,
)
from dagster._record import copy, record
from dagster.components.resolved.errors import ResolutionException

T = TypeVar("T")


class EnvScope:
    def __call__(self, key: str, default: Optional[Union[str, Any]] = ...) -> Optional[str]:
        value = os.environ.get(key, default=default)
        if value is ...:
            raise ResolutionException(
                f"Environment variable {key} is not set and no default value was provided."
                f" To provide a default value, use e.g. `env('{key}', 'default_value')`."
            )
        return value

    def __getattr__(self, key: str) -> Optional[str]:
        # jinja2 applies a hasattr check to any scope fn - we avoid raising our own exception
        # for this access
        if key.startswith("jinja"):
            raise AttributeError(f"{key} not found")

        return os.environ.get(key)

    def __getitem__(self, key: str) -> Optional[str]:
        raise ResolutionException(
            f"To access environment variables, use dot access or the `env` function, e.g. `env.{key}` or `env('{key}')`"
        )


def automation_condition_scope() -> Mapping[str, Any]:
    return {
        "eager": AutomationCondition.eager,
        "on_cron": AutomationCondition.on_cron,
    }


T = TypeVar("T")


@public
@record
class ResolutionContext:
    """The context available to Resolver functions when "resolving" from yaml in to a Resolvable object.
    This class should not be instantiated directly.

    Provides a `resolve_value` method that can be used to resolve templated values in a nested object before
    being transformed into the final Resolvable object. This is typically invoked inside a
    :py:class:`~dagster.Resolver`'s `resolve_fn` to ensure that jinja-templated values are turned into their
    respective python types using the available template variables.

    Example:

        .. code-block:: python

            import datetime
            import dagster as dg

            def resolve_timestamp(
                context: dg.ResolutionContext,
                raw_timestamp: str,
            ) -> datetime.datetime:
                return datetime.datetime.fromisoformat(
                    context.resolve_value(raw_timestamp, as_type=str),
                )

    """

    scope: Mapping[str, Any]
    path: list[Union[str, int]] = []
    source_position_tree: Optional[SourcePositionTree] = None
    # dict where you can stash arbitrary objects. Used to store references to ComponentLoadContext
    # We are structuring this way to make it easier to use Resolved outside of the context of
    # the component system in the future
    stash: dict[str, Any] = {}

    def at_path(self, path_part: Union[str, int]):
        return copy(self, path=[*self.path, path_part])

    @staticmethod
    def default(source_position_tree: Optional[SourcePositionTree] = None) -> "ResolutionContext":
        return ResolutionContext(
            scope={"env": EnvScope(), "automation_condition": automation_condition_scope()},
            source_position_tree=source_position_tree,
        )

    def with_stashed_value(self, key: str, value: Any) -> "ResolutionContext":
        return copy(self, stash={**self.stash, key: value})

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
        # defer for import performance
        from jinja2 import Undefined
        from jinja2.exceptions import UndefinedError
        from jinja2.nativetypes import NativeTemplate

        if (
            isinstance(val, str)
            and val  # evaluating empty string returns None so skip to preserve empty string values
        ):
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

    @public
    def resolve_value(self, val: Any, as_type: Optional[type] = None) -> Any:
        """Recursively resolves templated values in a nested object. This is typically
        invoked inside a :py:class:`~dagster.Resolver`'s `resolve_fn` to resolve all
        nested template values in the input object.

        Args:
            val (Any): The value to resolve.
            as_type (Optional[type]): If provided, the type to cast the resolved value to.
                Used purely for type hinting and does not impact runtime behavior.

        Returns:
            The input value after all nested template values have been resolved.
        """
        if isinstance(val, dict):
            return {k: self.at_path(k).resolve_value(v) for k, v in val.items()}
        elif isinstance(val, tuple):
            return tuple(self.at_path(i).resolve_value(v) for i, v in enumerate(val))
        elif isinstance(val, list):
            return [self.at_path(i).resolve_value(v) for i, v in enumerate(val)]
        else:
            return self._resolve_inner_value(val)

    def resolve_source_relative_path(self, value: str) -> Path:
        path = Path(value)
        if not self.source_position_tree or path.is_absolute():
            # no source, can't transform
            return path

        source_dir = Path(self.source_position_tree.position.filename).parent
        return source_dir.joinpath(path).resolve()
