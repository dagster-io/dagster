import tempfile
import webbrowser
from collections.abc import Iterator, Mapping, Sequence, Set
from typing import Any, Union

import markdown
import yaml

from dagster_dg.component import RemoteComponentType
from dagster_dg.yaml_utils import parse_yaml_with_source_positions
from dagster_dg.yaml_utils.source_position import SourcePositionTree

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
    json_schema: Mapping[str, Any], subschema: Mapping[str, Any]
) -> Any:
    subschema = _dereference_schema(json_schema, subschema)
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

    def write_line_break(self) -> None:
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
        {"type": component_type, "params": _sample_value_for_subschema(json_schema, json_schema)},
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


def render_markdown_in_browser(markdown_content: str) -> None:
    # Convert the markdown string to HTML
    html_content = markdown.markdown(markdown_content)

    # Add basic HTML structure
    full_html = f"""
    <!DOCTYPE html>
    <html lang="en">
    <head>
        <meta charset="UTF-8">
        <meta name="viewport" content="width=device-width, initial-scale=1.0">
        <title>Markdown Preview</title>
    </head>
    <body>
        {html_content}
    </body>
    </html>
    """

    # Create a temporary file
    with tempfile.NamedTemporaryFile(delete=False, suffix=".html") as temp_file:
        temp_file.write(full_html.encode("utf-8"))
        temp_file_path = temp_file.name

    # Open the temporary file in the default web browser
    webbrowser.open(f"file://{temp_file_path}")


def markdown_for_component_type(remote_component_type: RemoteComponentType) -> str:
    component_type_name = f"{remote_component_type.package}.{remote_component_type.name}"
    sample_yaml = generate_sample_yaml(
        component_type_name, remote_component_type.component_params_schema or {}
    )
    rows = len(sample_yaml.split("\n")) + 1
    return f"""
## Component: `{component_type_name}`
 
### Description: 
{remote_component_type.description}

### Sample Component Params:

<textarea rows={rows} cols=100>
{sample_yaml}
</textarea>
"""
