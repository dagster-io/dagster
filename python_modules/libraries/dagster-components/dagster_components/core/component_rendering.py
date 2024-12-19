import json
import os
from typing import AbstractSet, Any, Mapping, Optional, Sequence, Type, TypeVar, Union

import dagster._check as check
from dagster._record import record
from jinja2 import Template
from pydantic import BaseModel, Field
from pydantic.fields import FieldInfo

T = TypeVar("T")

REF_BASE = "#/$defs/"
REF_TEMPLATE = f"{REF_BASE}{{model}}"

CONTEXT_KEY = "required_rendering_scope"


def RenderingScope(field: Optional[FieldInfo] = None, *, required_scope: AbstractSet[str]) -> Any:
    """Defines a Pydantic Field that requires a specific scope to be available before rendering.

    Examples:
    ```python
    class Schema(BaseModel):
        a: str = RenderingScope(required_scope={"foo", "bar"})
        b: Optional[int] = RenderingScope(Field(default=None), required_scope={"baz"})
    ```
    """
    return FieldInfo.merge_field_infos(
        field or Field(), Field(json_schema_extra={CONTEXT_KEY: json.dumps(list(required_scope))})
    )


def get_required_rendering_context(subschema: Mapping[str, Any]) -> Optional[AbstractSet[str]]:
    raw = check.opt_inst(subschema.get(CONTEXT_KEY), str)
    return set(json.loads(raw)) if raw else None


def _env(key: str) -> Optional[str]:
    return os.environ.get(key)


@record
class TemplatedValueResolver:
    context: Mapping[str, Any]

    @staticmethod
    def default() -> "TemplatedValueResolver":
        return TemplatedValueResolver(context={"env": _env})

    def with_context(self, **additional_context) -> "TemplatedValueResolver":
        return TemplatedValueResolver(context={**self.context, **additional_context})

    def resolve(self, val: str) -> str:
        return Template(val).render(**self.context)


def _should_render(
    valpath: Sequence[Union[str, int]], json_schema: Mapping[str, Any], subschema: Mapping[str, Any]
) -> bool:
    # List[ComplexType] (e.g.) will contain a reference to the complex type schema in the
    # top-level $defs, so we dereference it here.
    if "$ref" in subschema:
        subschema = json_schema["$defs"].get(subschema["$ref"][len(REF_BASE) :])

    if get_required_rendering_context(subschema) is not None:
        return False
    elif len(valpath) == 0:
        return True

    # Optional[ComplexType] (e.g.) will contain multiple schemas in the "anyOf" field
    if "anyOf" in subschema:
        return any(_should_render(valpath, json_schema, inner) for inner in subschema["anyOf"])

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

    # the path wasn't valid
    if not inner:
        return False

    _, *rest = valpath
    return _should_render(rest, json_schema, inner)


def _render_values(
    value_resolver: TemplatedValueResolver,
    val: Any,
    valpath: Sequence[Union[str, int]],
    json_schema: Optional[Mapping[str, Any]],
) -> Any:
    if json_schema and not _should_render(valpath, json_schema, json_schema):
        return val
    elif isinstance(val, dict):
        return {
            k: _render_values(value_resolver, v, [*valpath, k], json_schema) for k, v in val.items()
        }
    elif isinstance(val, list):
        return [
            _render_values(value_resolver, v, [*valpath, i], json_schema) for i, v in enumerate(val)
        ]
    else:
        return value_resolver.resolve(val)


def preprocess_value(renderer: TemplatedValueResolver, val: T, target_type: Type) -> T:
    """Given a raw value, preprocesses it by rendering any templated values that are not marked as deferred in the target_type's json schema."""
    json_schema = target_type.model_json_schema() if issubclass(target_type, BaseModel) else None
    return _render_values(renderer, val, [], json_schema)
