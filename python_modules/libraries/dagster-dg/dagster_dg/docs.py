import copy
import json
import tempfile
import textwrap
import webbrowser
from collections.abc import Iterator, Mapping, Sequence, Set
from typing import Any, Optional, Union

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


def html_from_markdown(markdown_content: str) -> str:
    # Convert the markdown string to HTML
    html_content = markdown.markdown(markdown_content)

    # Add basic HTML structure
    full_html = (
        """
    <!DOCTYPE html>
    <html lang="en">
    <head>
        <meta charset="UTF-8">
        <meta name="viewport" content="width=device-width, initial-scale=1.0">
        <title>Markdown Preview</title>
        <style>
            body {
                font-weight: 400;
                font-family: "Geist", "Inter", "Arial", sans-serif;
                font-size: 16px;
            }
            textarea {
                max-width: 100%;
                font-family: ui-monospace, SFMono-Regular, Consolas, 'Liberation Mono', Menlo, monospace;
                border: none;
                background-color: rgb(246, 248, 250);
                border-radius: 6px;
                padding: 16px;
            }
        </style>
    </head>
    <body>
        <div style="max-width: 75%; margin: 0 auto;">"""
        + html_content
        + """</div>
    </body>
    </html>
    """
    )
    return full_html


def open_html_in_browser(html_content: str) -> None:
    # Create a temporary file
    with tempfile.NamedTemporaryFile(delete=False, suffix=".html") as temp_file:
        temp_file.write(html_content.encode("utf-8"))
        temp_file_path = temp_file.name

    # Open the temporary file in the default web browser
    webbrowser.open(f"file://{temp_file_path}")


def process_description(description: str) -> str:
    return description.replace("\n", "<br>")


def markdown_for_json_schema(
    key: str,
    json_schema: Mapping[str, Any],
    subschema: Mapping[str, Any],
    anyof_parent_subschema: Optional[Mapping[str, Any]] = None,
    indent: int = 0,
    is_list: bool = False,
    is_nullable: bool = False,
) -> str:
    """Produces a nested markdown list of the subschema, including component-author-provided description and examples.
    Uses <details> blocks to collapse nested fields by default.

    Args:
        key: The key of the current field in the schema.
        json_schema: The complete schema.
        subschema: The current field's schema.
        anyof_parent_subschema: The parent schema, if the current field is part of an anyOf.
        indent: The indentation level for the current field.
        is_list: Whether the current field is a list.
        is_nullable: Whether the current field is nullable.
    """
    subschema = _dereference_schema(json_schema, subschema)

    if "anyOf" in subschema:
        # TODO: handle anyOf fields more gracefully, for now just choose first option
        is_nullable = any(nested.get("type") == "null" for nested in subschema["anyOf"])
        return markdown_for_json_schema(
            key,
            json_schema,
            subschema["anyOf"][0],
            anyof_parent_subschema=subschema,
            indent=indent,
            is_nullable=is_nullable,
        )

    objtype = subschema["type"]

    children = ""
    if objtype == "object":
        children = "\n".join(
            [
                markdown_for_json_schema(k, json_schema, v, indent=indent + 2)
                for k, v in subschema.get("properties", {}).items()
            ]
        )
    elif objtype == "array":
        return markdown_for_json_schema(key, json_schema, subschema["items"], is_list=True)

    description = process_description(
        subschema.get("description", "") or (anyof_parent_subschema or {}).get("description", "")
    )
    # use dedent to remove the leading newline
    children_segment = (
        textwrap.dedent(f"""
            <details>
            <summary>Subfields</summary>
            \n\n
            <ul>
            {children}
            </ul>
            </details>
        """).strip()
        if children
        else ""
    )
    examples = subschema.get("examples", []) or (anyof_parent_subschema or {}).get("examples", [])
    examples_segment = (
        f"Example: <code>{json.dumps(examples[0], indent=2)}</code>" if examples else ""
    )

    body = "<br/>".join(x for x in [description, examples_segment, children_segment] if x)
    body = textwrap.indent("<br/>" + body + "", prefix="  ") if body else ""

    type_str = f"[{subschema['type']}]" if is_list else subschema["type"]
    if is_nullable:
        type_str = f"{type_str} | null"
    output = f"""<li><strong>{key}</strong> - <code>{type_str}</code>{body}</li>\n"""
    # indent the output with textwrap
    return textwrap.indent(output, " " * indent)


def markdown_for_param_types(remote_component_type: RemoteComponentType) -> str:
    schema = remote_component_type.component_schema or {}
    return f"<ul>{markdown_for_json_schema('attributes', schema, schema)}</ul>"


def markdown_for_component_type(remote_component_type: RemoteComponentType) -> str:
    component_type_name = f"{remote_component_type.namespace}.{remote_component_type.name}"
    sample_yaml = generate_sample_yaml(
        component_type_name, remote_component_type.component_schema or {}
    )
    rows = len(sample_yaml.split("\n")) + 1
    return f"""
## Component: `{component_type_name}`

### Description:
{remote_component_type.description}

### Component Schema:

{markdown_for_param_types(remote_component_type)}

### Sample Component YAML:

<textarea rows={rows} cols=100>
{sample_yaml}
</textarea>
"""
