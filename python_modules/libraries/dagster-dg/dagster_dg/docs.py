import tempfile
import webbrowser
from collections.abc import Mapping, Sequence, Set
from dataclasses import dataclass
from typing import Any, Optional, Union

import markdown
import yaml

from dagster_dg.component import RemoteComponentType

REF_BASE = "#/$defs/"
COMMENTED_MAPPING_TAG = "!commented_mapping"


@dataclass(frozen=True)
class CommentedObject:
    key: str
    value: Union[Sequence["CommentedObject"], Any]
    comment: Optional[str]
    top_level: bool = False


def _dereference_schema(
    json_schema: Mapping[str, Any], subschema: Mapping[str, Any]
) -> Mapping[str, Any]:
    if "$ref" in subschema:
        return json_schema["$defs"].get(subschema["$ref"][len(REF_BASE) :])
    else:
        return subschema


def _commented_object_for_subschema(
    name: str,
    json_schema: Mapping[str, Any],
    subschema: Mapping[str, Any],
    available_scope: Optional[Set[str]] = None,
) -> Union[CommentedObject, Any]:
    additional_scope = subschema.get("dagster_available_scope")
    available_scope = (available_scope or set()) | set(additional_scope or [])

    subschema = _dereference_schema(json_schema, subschema)
    if "anyOf" in subschema:
        # TODO: handle anyOf fields more gracefully, for now just choose first option
        return _commented_object_for_subschema(
            name, json_schema, subschema["anyOf"][0], available_scope=available_scope
        )

    objtype = subschema["type"]
    if objtype == "object":
        return CommentedObject(
            key=name,
            value={
                k: _commented_object_for_subschema(k, json_schema, v)
                for k, v in subschema.get("properties", {}).items()
            },
            comment=f"Available scope: {available_scope}" if available_scope else None,
        )
    elif objtype == "array":
        return [
            _commented_object_for_subschema(
                name, json_schema, subschema["items"], available_scope=available_scope
            )
        ]
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

    def _get_tag(self) -> str:
        return getattr(self.event, "tag", "")

    def expect_node(self, root=False, sequence=False, mapping=False, simple_key=False):
        # for commented mappings, emit comment above the value
        tag = self._get_tag()
        if tag.startswith(COMMENTED_MAPPING_TAG):
            self.write_indicator(f"# {tag[len(COMMENTED_MAPPING_TAG) + 1:]}", True)
            self.write_line_break()

        return super().expect_node(root, sequence, mapping, simple_key)

    def process_tag(self):
        tag = self._get_tag()
        # ignore the mapping tag as it's handled specially
        if tag.startswith(COMMENTED_MAPPING_TAG):
            return
        else:
            super().process_tag()


def commented_object_representer(dumper: yaml.SafeDumper, obj: CommentedObject) -> yaml.nodes.Node:
    mapping = obj.value if isinstance(obj.value, dict) else {obj.key: obj.value}

    if obj.comment is not None:
        return dumper.represent_mapping(f"{COMMENTED_MAPPING_TAG}|{obj.comment}", mapping)
    else:
        return dumper.represent_dict(mapping)


ComponentDumper.add_representer(CommentedObject, commented_object_representer)


def generate_sample_yaml(component_type: str, json_schema: Mapping[str, Any]) -> str:
    params_obj = _commented_object_for_subschema("params", json_schema, json_schema)
    return yaml.dump(
        {"type": component_type, "params": params_obj}, Dumper=ComponentDumper, sort_keys=False
    )


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
