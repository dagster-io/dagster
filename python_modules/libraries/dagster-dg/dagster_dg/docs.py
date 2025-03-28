import copy
import json
from collections.abc import Iterator, Mapping, Sequence, Set
from itertools import groupby
from typing import Any, Optional, TypedDict, Union

import yaml
from dagster_shared.serdes.objects import LibraryObjectKey
from dagster_shared.yaml_utils import parse_yaml_with_source_positions
from dagster_shared.yaml_utils.source_position import SourcePositionTree

from dagster_dg.component import ComponentTypeSnap, RemoteLibraryObjectRegistry

REF_BASE = "#/$defs/"
JSON_SCHEMA_EXTRA_REQUIRED_SCOPE_KEY = "dagster_required_scope"


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
        raise ValueError(f"Invalid valpath element: {el}")

    # the path wasn't valid, or unspecified
    if not inner:
        return

    _, *rest = valpath
    yield from _subschemas_on_path(rest, json_schema, inner)


def _get_additional_required_scope(subschema: Mapping[str, Any]) -> Set[str]:
    raw = subschema.get(JSON_SCHEMA_EXTRA_REQUIRED_SCOPE_KEY)
    return set(raw) if raw else set()


def get_required_scope(
    valpath: Sequence[Union[str, int]], json_schema: Mapping[str, Any]
) -> Set[str]:
    """Given a valpath and the json schema of a given target type, determines the available rendering scope."""
    required_scope = set()
    for subschema in _subschemas_on_path(valpath, json_schema, json_schema):
        required_scope |= _get_additional_required_scope(subschema)
    return required_scope


def _dereference_schema(
    json_schema: Mapping[str, Any], subschema: Mapping[str, Any]
) -> Mapping[str, Any]:
    if "$ref" in subschema:
        return json_schema["$defs"].get(subschema["$ref"][len(REF_BASE) :])
    else:
        return subschema


def _sample_value_for_subschema(
    json_schema: Mapping[str, Any],
    subschema: Mapping[str, Any],
) -> Any:
    example_value = next(iter(subschema.get("examples", [])), None)

    subschema = _dereference_schema(json_schema, subschema)

    if example_value:
        return copy.deepcopy(example_value)
    if "anyOf" in subschema:
        # TODO: handle anyOf fields more gracefully, for now just choose first option
        return _sample_value_for_subschema(json_schema, subschema["anyOf"][0])

    objtype = subschema["type"]
    if objtype == "object":
        return {
            k: _sample_value_for_subschema(json_schema, v)
            for k, v in subschema.get("properties", {}).items()
        }
    elif objtype == "array":
        return [_sample_value_for_subschema(json_schema, subschema["items"])]
    elif objtype == "string":
        return "..."
    elif objtype == "integer":
        return 0
    elif objtype == "boolean":
        return False
    else:
        return f"({objtype})"


class ComponentDumper(yaml.SafeDumper):
    def increase_indent(self, flow=False, *args, **kwargs):
        # makes the output somewhat prettier by forcing lists to be indented
        return super().increase_indent(flow=flow, indentless=False)

    def write_line_break(self) -> None:  # pyright: ignore[reportIncompatibleMethodOverride]
        # add an extra line break between top-level keys
        if self.indent == 0:
            super().write_line_break()
        super().write_line_break()


def _get_source_position_comments(
    valpath: Sequence[Union[str, int]], tree: SourcePositionTree, json_schema: Mapping[str, Any]
) -> Iterator[tuple[int, str]]:
    available_scope = get_required_scope(valpath[1:], json_schema)
    if available_scope:
        yield (tree.position.start.line - 1, f"Available scope: {available_scope}")
    for child_path, child_tree in tree.children.items():
        yield from _get_source_position_comments([*valpath, child_path], child_tree, json_schema)


def generate_sample_yaml(component_type: str, json_schema: Mapping[str, Any]) -> str:
    raw = yaml.dump(
        {
            "type": component_type,
            "attributes": _sample_value_for_subschema(json_schema, json_schema),
        },
        Dumper=ComponentDumper,
        sort_keys=False,
    )
    parsed = parse_yaml_with_source_positions(raw)
    comments = dict(_get_source_position_comments([], parsed.source_position_tree, json_schema))
    commented_lines = []
    for line_num, line in enumerate(raw.split("\n")):
        if line_num in comments:
            commented_lines.append(f"{line} # {comments[line_num]}")
        else:
            commented_lines.append(line)
    return "\n".join(commented_lines)


class ComponentTypeJson(TypedDict):
    """Component type JSON, used to back dg docs webapp."""

    name: str
    author: str
    tags: list[str]
    example: str
    schema: str
    description: Optional[str]


class ComponentTypeNamespaceJson(TypedDict):
    """Component type namespace JSON, used to back dg docs webapp."""

    name: str
    componentTypes: list[ComponentTypeJson]


def json_for_all_components(
    registry: RemoteLibraryObjectRegistry,
) -> list[ComponentTypeNamespaceJson]:
    """Returns a list of JSON representations of all component types in the registry."""
    component_json = [
        (key.namespace.split(".")[0], json_for_component_type(key, library_obj))
        for key, library_obj in registry.items()
        if isinstance(library_obj, ComponentTypeSnap) and library_obj.schema is not None
    ]
    return [
        ComponentTypeNamespaceJson(
            name=namespace,
            componentTypes=[namespace_and_component[1] for namespace_and_component in components],
        )
        for namespace, components in groupby(component_json, key=lambda x: x[0])
    ]


def json_for_component_type(
    key: LibraryObjectKey, remote_component_type: ComponentTypeSnap
) -> ComponentTypeJson:
    typename = key.to_typename()
    sample_yaml = generate_sample_yaml(typename, remote_component_type.schema or {})
    return ComponentTypeJson(
        name=typename,
        author="",
        tags=[],
        example=sample_yaml,
        schema=json.dumps(remote_component_type.schema),
        description=remote_component_type.description,
    )
