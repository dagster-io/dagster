import functools
import os
import typing
from collections.abc import Iterator, Mapping, Sequence, Set
from dataclasses import dataclass
from typing import Annotated, Any, Callable, Optional, TypeVar, Union, get_origin

import dagster._check as check
from dagster._core.definitions.declarative_automation.automation_condition import (
    AutomationCondition,
)
from dagster._record import record
from jinja2.nativetypes import NativeTemplate
from pydantic import BaseModel, ConfigDict, TypeAdapter
from pydantic.fields import FieldInfo

T = TypeVar("T")

REF_BASE = "#/$defs/"
REF_TEMPLATE = f"{REF_BASE}{{model}}"

JSON_SCHEMA_EXTRA_DEFER_RENDERING_KEY = "dagster_defer_rendering"
JSON_SCHEMA_EXTRA_AVAILABLE_SCOPE_KEY = "dagster_available_scope"


def automation_condition_scope() -> Mapping[str, Any]:
    return {
        "eager": AutomationCondition.eager,
        "on_cron": AutomationCondition.on_cron,
    }


def _should_defer_render(subschema: Mapping[str, Any]) -> bool:
    raw = check.opt_inst(subschema.get(JSON_SCHEMA_EXTRA_DEFER_RENDERING_KEY), bool)
    return raw or False


def _get_available_scope(subschema: Mapping[str, Any]) -> Set[str]:
    raw = check.opt_inst(subschema.get(JSON_SCHEMA_EXTRA_AVAILABLE_SCOPE_KEY), list)
    return set(raw) if raw else set()


def _env(key: str) -> Optional[str]:
    return os.environ.get(key)


ShouldResolveFn = Callable[[Sequence[Union[str, int]]], bool]


@dataclass
class ResolutionMetadata:
    """Internal class that stores arbitrary metadata about a resolved field."""

    output_type: type
    post_process: Optional[Callable[[Any], Any]] = None


class ResolvedFieldInfo(FieldInfo):
    """Wrapper class that stores additional resolution metadata within a pydantic FieldInfo object."""

    def __init__(
        self,
        *,
        output_type: Optional[type] = None,
        post_process_fn: Optional[Callable[[Any], Any]] = None,
        additional_scope: Optional[Set[str]] = None,
    ):
        self.resolution_metadata = (
            ResolutionMetadata(output_type=output_type, post_process=post_process_fn)
            if output_type
            else None
        )
        super().__init__(
            json_schema_extra={
                JSON_SCHEMA_EXTRA_AVAILABLE_SCOPE_KEY: list(additional_scope or []),
                JSON_SCHEMA_EXTRA_DEFER_RENDERING_KEY: True,
            },
        )


def _get_resolution_metadata(annotation: type) -> ResolutionMetadata:
    origin = get_origin(annotation)
    if origin is Annotated:
        _, f_metadata, *_ = typing.get_args(annotation)
        if isinstance(f_metadata, ResolvedFieldInfo) and f_metadata.resolution_metadata:
            return f_metadata.resolution_metadata
    return ResolutionMetadata(output_type=annotation)


class ComponentSchemaBaseModel(BaseModel):
    """Base class for models that are part of a component schema."""

    model_config = ConfigDict(json_schema_extra={JSON_SCHEMA_EXTRA_DEFER_RENDERING_KEY: True})

    def render_properties(self, value_resolver: "TemplatedValueResolver") -> Mapping[str, Any]:
        """Returns a dictionary of resolved properties for this class."""
        raw_properties = self.model_dump(exclude_unset=True)

        # validate that the resolved properties match the output type
        resolved_properties = {}
        for k, v in raw_properties.items():
            resolved = value_resolver.render_obj(v)
            annotation = self.__annotations__[k]
            rendering_metadata = _get_resolution_metadata(annotation)

            if rendering_metadata.post_process:
                resolved = rendering_metadata.post_process(resolved)

            # hook into pydantic's type validation to handle complicated stuff like Optional[Mapping[str, int]]
            TypeAdapter(
                rendering_metadata.output_type, config={"arbitrary_types_allowed": True}
            ).validate_python(resolved)

            resolved_properties[k] = resolved

        return resolved_properties


@record
class TemplatedValueResolver:
    context: Mapping[str, Any]

    @staticmethod
    def default() -> "TemplatedValueResolver":
        return TemplatedValueResolver(
            context={"env": _env, "automation_condition": automation_condition_scope()}
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
            return self._render_value(obj)

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


def _subschemas_on_path(
    valpath: Sequence[Union[str, int]], json_schema: Mapping[str, Any], subschema: Mapping[str, Any]
) -> Iterator[Mapping[str, Any]]:
    """Given a valpath and the json schema of a given target type, returns the subschemas at each step of the path."""
    # List[ComplexType] (e.g.) will contain a reference to the complex type schema in the
    # top-level $defs, so we dereference it here.
    if "$ref" in subschema:
        subschema = json_schema["$defs"].get(subschema["$ref"][len(REF_BASE) :])

    yield subschema
    if len(valpath) == 0:
        return

    # Optional[ComplexType] (e.g.) will contain multiple schemas in the "anyOf" field
    if "anyOf" in subschema:
        for inner in subschema["anyOf"]:
            yield from _subschemas_on_path(valpath, json_schema, inner)

    el = valpath[0]
    if isinstance(el, str):
        # valpath: ['field']
        # field: X
        inner = subschema.get("properties", {}).get(el)
    elif isinstance(el, int):
        # valpath: ['field', 0]
        # field: List[X]
        inner = subschema.get("items")
    else:
        check.failed(f"Unexpected valpath element: {el}")

    # the path wasn't valid, or unspecified
    if not inner:
        return

    _, *rest = valpath
    yield from _subschemas_on_path(rest, json_schema, inner)


def allow_render(
    valpath: Sequence[Union[str, int]], json_schema: Mapping[str, Any], subschema: Mapping[str, Any]
) -> bool:
    """Given a valpath and the json schema of a given target type, determines if there is a rendering scope
    required to render the value at the given path.
    """
    for subschema in _subschemas_on_path(valpath, json_schema, subschema):
        if _should_defer_render(subschema):
            return False
    return True


def get_available_scope(
    valpath: Sequence[Union[str, int]], json_schema: Mapping[str, Any], subschema: Mapping[str, Any]
) -> Set[str]:
    """Given a valpath and the json schema of a given target type, determines the available rendering scope."""
    available_scope = set()
    for subschema in _subschemas_on_path(valpath, json_schema, subschema):
        available_scope |= _get_available_scope(subschema)
    return available_scope
