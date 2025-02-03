from collections.abc import Iterator, Mapping, Sequence, Set
from dataclasses import dataclass
from typing import Annotated, Any, Callable, Optional, Union, get_args, get_origin

import dagster._check as check
from pydantic.fields import FieldInfo

REF_BASE = "#/$defs/"
REF_TEMPLATE = f"{REF_BASE}{{model}}"
JSON_SCHEMA_EXTRA_REQUIRED_SCOPE_KEY = "dagster_required_scope"


@dataclass
class ResolutionMetadata:
    """Internal class that stores arbitrary metadata about a resolved field."""

    output_type: type
    post_process: Optional[Callable[[Any], Any]] = None


class ResolvableFieldInfo(FieldInfo):
    """Wrapper class that stores additional resolution metadata within a pydantic FieldInfo object.

    Examples:
    ```python
    class MyModel(ResolvableModel):
        resolvable_obj: Annotated[str, ResolvableFieldInfo(output_type=SomeObj)]
    ```
    """

    def __init__(
        self,
        *,
        output_type: Optional[type] = None,
        post_process_fn: Optional[Callable[[Any], Any]] = None,
        required_scope: Optional[Set[str]] = None,
    ):
        self.resolution_metadata = (
            ResolutionMetadata(output_type=output_type, post_process=post_process_fn)
            if output_type
            else None
        )
        super().__init__(
            json_schema_extra={JSON_SCHEMA_EXTRA_REQUIRED_SCOPE_KEY: list(required_scope or [])},
        )


def get_resolution_metadata(annotation: type) -> ResolutionMetadata:
    origin = get_origin(annotation)
    if origin is Annotated:
        _, f_metadata, *_ = get_args(annotation)
        if isinstance(f_metadata, ResolvableFieldInfo) and f_metadata.resolution_metadata:
            return f_metadata.resolution_metadata
    return ResolutionMetadata(output_type=annotation)


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
