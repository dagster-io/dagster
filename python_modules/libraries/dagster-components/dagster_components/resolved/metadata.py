import inspect
from collections.abc import Iterator, Mapping, Sequence, Set
from dataclasses import dataclass
from inspect import Parameter
from typing import Any, Optional, Union

import dagster._check as check
from pydantic.fields import FieldInfo
from typing_extensions import get_args

REF_BASE = "#/$defs/"
REF_TEMPLATE = f"{REF_BASE}{{model}}"
JSON_SCHEMA_EXTRA_REQUIRED_SCOPE_KEY = "dagster_required_scope"


@dataclass
class ScopeMetadata:
    scope_type: type = Any
    description: Optional[str] = None
    scope_parameters: Optional[Mapping[str, Parameter]] = None
    scope_return_type: Optional[type] = None

    def to_json(self) -> dict[str, Any]:
        return {
            "scope_type": get_str_representation(self.scope_type),
            "description": self.description,
            "scope_parameters": (
                {
                    k: {
                        "name": k,
                        "type": get_str_representation(v.annotation),
                        **(
                            {"default": str(v.default)}
                            if v.default is not inspect.Parameter.empty
                            else {}
                        ),
                    }
                    for k, v in self.scope_parameters.items()
                }
                if self.scope_parameters
                else None
            ),
            "scope_return_type": get_str_representation(self.scope_return_type)
            if self.scope_return_type
            else None,
        }


def get_str_representation(typ: type) -> str:
    args = get_args(typ)

    if len(args) == 0:
        return typ.__name__
    else:
        return f"{typ.__name__}[{', '.join(get_str_representation(arg) for arg in args)}]"


class ResolvableFieldInfo(FieldInfo):
    """Wrapper class that stores additional resolution metadata within a pydantic FieldInfo object.

    Examples:
    ```python
    class MyModel(ComponentSchema):
        resolvable_obj: Annotated[str, ResolvableFieldInfo(required_scope={"some_field"})]
    ```
    """

    def __init__(
        self,
        *,
        required_scope: Optional[Union[dict[str, ScopeMetadata], set[str]]] = None,
    ):
        required_scope = (
            {key: ScopeMetadata() for key in required_scope}
            if isinstance(required_scope, set)
            else required_scope
        )
        super().__init__(
            json_schema_extra={
                JSON_SCHEMA_EXTRA_REQUIRED_SCOPE_KEY: {
                    scope_name: scope_metadata.to_json()
                    for scope_name, scope_metadata in (required_scope or {}).items()
                }
            },
        )


def _subschemas_on_path(
    valpath: Sequence[Union[str, int]], json_schema: Mapping[str, Any], subschema: Mapping[str, Any]
) -> Iterator[Mapping[str, Any]]:
    """Given a valpath and the json schema of a given target type, returns the subschemas at each step of the path."""
    # List[ComplexType] (e.g.) will contain a reference to the complex type schema in the
    # top-level $defs, so we dereference it here.
    if "$ref" in subschema:
        # depending on the pydantic version, the extras may be stored with the reference or not
        extras = {k: v for k, v in subschema.items() if k != "$ref"}
        subschema = {**json_schema["$defs"].get(subschema["$ref"][len(REF_BASE) :]), **extras}

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


def _get_additional_required_scope(subschema: Mapping[str, Any]) -> Set[str]:
    raw = check.opt_inst(subschema.get(JSON_SCHEMA_EXTRA_REQUIRED_SCOPE_KEY), list)
    return set(raw) if raw else set()


def get_required_scope(
    valpath: Sequence[Union[str, int]], json_schema: Mapping[str, Any]
) -> Set[str]:
    """Given a valpath and the json schema of a given target type, determines the available rendering scope."""
    required_scope = set()
    for subschema in _subschemas_on_path(valpath, json_schema, json_schema):
        required_scope |= _get_additional_required_scope(subschema)
    return required_scope
