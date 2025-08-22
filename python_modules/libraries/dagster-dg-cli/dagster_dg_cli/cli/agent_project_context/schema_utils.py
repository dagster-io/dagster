"""Utilities for generating YAML templates from JSON schemas."""

from typing import Any

import click


def print_simplified_schema(schema: dict[str, Any]) -> None:
    """Print a simplified version of a JSON schema."""
    properties = schema.get("properties", {})
    if not properties:
        click.echo("  (No configuration properties defined)")
        return

    required_props = set(schema.get("required", []))

    for prop_name, prop_info in list(properties.items())[:8]:  # Show first 8 properties
        prop_type = prop_info.get("type", "unknown")
        is_required = prop_name in required_props
        required_marker = " **(required)**" if is_required else ""

        description = prop_info.get("description", "")
        if description and len(description) > 80:
            description = description[:77] + "..."

        type_info = f"`{prop_type}`"
        if prop_type == "array" and "items" in prop_info:
            item_type = prop_info["items"].get("type", "unknown")
            type_info = f"`array of {item_type}`"
        elif prop_type == "object" and "properties" in prop_info:
            type_info = "`object`"

        line = f"  • **{prop_name}** ({type_info}){required_marker}"
        if description:
            line += f": {description}"
        click.echo(line)

    if len(properties) > 8:
        click.echo(f"  ...and {len(properties) - 8} more properties")


def generate_yaml_template_from_schema(schema: dict[str, Any], component_name: str) -> str:
    """Generate a YAML template with comments from a JSON schema."""
    lines = []
    lines.append(f"# Template for {component_name}")
    lines.append("")

    properties = schema.get("properties", {})
    required_props = set(schema.get("required", []))
    defs = schema.get("$defs", {})

    def _resolve_ref(ref_path: str) -> dict[str, Any]:
        """Resolve a $ref path to the actual definition."""
        if ref_path.startswith("#/$defs/"):
            def_name = ref_path.split("/")[-1]
            return defs.get(def_name, {})
        return {}

    def _resolve_type_info(prop_info: dict[str, Any]) -> tuple[str, str, Any]:
        """Return (yaml_type, comment_type, example_value)."""
        # Handle anyOf (union types)
        if "anyOf" in prop_info:
            non_null_types = [t for t in prop_info["anyOf"] if t.get("type") != "null"]

            if len(non_null_types) == 1:
                # Single non-null type
                main_type = non_null_types[0]
                return _resolve_type_info(main_type)
            else:
                # Multiple types - prefer object types for expansion, then fall back to primitives
                object_type = None
                primitive_type = None

                for t in non_null_types:
                    if "$ref" in t:
                        # Reference to object definition - use this for expansion
                        ref_path = t["$ref"]
                        def_name = ref_path.split("/")[-1]
                        resolved_def = _resolve_ref(ref_path)
                        object_type = ("object", f"object ({def_name})", resolved_def)
                        break
                    elif t.get("type") == "object":
                        # Direct object definition
                        nested_props = t.get("properties", {})
                        object_type = ("object", "object", nested_props)
                        break
                    elif (
                        t.get("type") in ["string", "integer", "number", "boolean", "array"]
                        and not primitive_type
                    ):
                        # Keep the first primitive type as fallback
                        primitive_type = _resolve_type_info(t)

                # If we found an object type, use that for expansion with union comment
                if object_type:
                    yaml_type, _, example_value = object_type
                    type_names = []
                    for t in non_null_types:
                        if "$ref" in t:
                            type_names.append("object")
                        else:
                            type_names.append(t.get("type", "object"))
                    comment_type = " | ".join(type_names)
                    return yaml_type, comment_type, example_value
                elif primitive_type:
                    yaml_type, _, example = primitive_type
                    type_names = [t2.get("type", "object") for t2 in non_null_types]
                    comment_type = " | ".join(type_names)
                    return yaml_type, comment_type, example

                # Fallback to string for complex unions
                return "string", "string", '""'

        # Handle $ref (references to definitions)
        if "$ref" in prop_info:
            ref_path = prop_info["$ref"]
            def_name = ref_path.split("/")[-1]
            resolved_def = _resolve_ref(ref_path)
            return "object", f"object ({def_name})", resolved_def

        prop_type = prop_info.get("type", "string")

        if prop_type == "string":
            if prop_info.get("const"):
                return "string", "string", f'"{prop_info["const"]}"'
            examples = prop_info.get("examples", [])
            if examples:
                return (
                    "string",
                    "string",
                    f'"{examples[0]}"' if isinstance(examples[0], str) else str(examples[0]),
                )
            return "string", "string", '""'
        elif prop_type == "integer":
            default = prop_info.get("default", 0)
            return "integer", "integer", str(default)
        elif prop_type == "number":
            default = prop_info.get("default", 0.0)
            return "number", "number", str(default)
        elif prop_type == "boolean":
            default = prop_info.get("default", False)
            return "boolean", "boolean", str(default).lower()
        elif prop_type == "array":
            items_info = prop_info.get("items", {})
            if "$ref" in items_info:
                ref_def = _resolve_ref(items_info["$ref"])
                item_type = f"object ({items_info['$ref'].split('/')[-1]})"
                return "array", f"array of {item_type}", [ref_def]
            else:
                item_type = items_info.get("type", "string")
                return "array", f"array of {item_type}", []
        elif prop_type == "object":
            nested_props = prop_info.get("properties", {})
            return "object", "object", nested_props
        else:
            return "string", prop_type, '""'

    def _add_properties(props: dict[str, Any], required: set[str], indent: int = 0) -> None:
        """Recursively add properties to the template."""
        prefix = "  " * indent

        for prop_name, prop_info in props.items():
            is_required = prop_name in required
            default_val = prop_info.get("default")
            description = prop_info.get("description", "")

            yaml_type, comment_type, example_value = _resolve_type_info(prop_info)

            # Build comment with requirement info
            comment_parts = [comment_type]
            if is_required:
                comment_parts.append("Required")
            else:
                if default_val is not None and default_val != "__DAGSTER_UNSET_DEFAULT__":
                    comment_parts.append(f"Default: {default_val}")
                else:
                    comment_parts.append("Optional")

            if description:
                # Truncate long descriptions
                desc = description[:50] + "..." if len(description) > 50 else description
                comment_parts.append(desc)

            comment = " # " + "; ".join(comment_parts)

            # Generate template line
            if yaml_type == "array":
                lines.append(f"{prefix}{prop_name}:{comment}")
                if (
                    isinstance(example_value, list)
                    and example_value
                    and isinstance(example_value[0], dict)
                ):
                    # Array of objects - expand the first object
                    lines.append(f"{prefix}  -")
                    nested_props = example_value[0].get("properties", {})
                    nested_required = set(example_value[0].get("required", []))
                    if nested_props:
                        _add_properties(nested_props, nested_required, indent + 2)
                else:
                    item_type = (
                        comment_type.split(" of ")[1] if " of " in comment_type else "string"
                    )
                    lines.append(f"{prefix}  - {item_type}")
            elif yaml_type == "object":
                lines.append(f"{prefix}{prop_name}:{comment}")
                # Expand nested object properties
                if isinstance(example_value, dict):
                    nested_props = example_value.get("properties", {})
                    nested_required = set(example_value.get("required", []))
                    if nested_props:
                        _add_properties(nested_props, nested_required, indent + 1)
                    else:
                        lines.append(f"{prefix}  key: value")
                else:
                    lines.append(f"{prefix}  key: value")
            else:
                lines.append(f"{prefix}{prop_name}: {comment_type}{comment}")

    # Add all properties with template syntax
    _add_properties(properties, required_props)

    # Add example section with realistic values
    lines.append("")
    lines.append("# Example Values:")

    def _generate_full_example(
        props: dict[str, Any], required: set[str], indent: int = 0
    ) -> list[str]:
        """Recursively generate a complete example document from schema."""
        example_lines = []
        prefix = "  " * indent

        for prop_name, prop_info in props.items():
            yaml_type, _, example_obj = _resolve_type_info(prop_info)

            # Use schema examples if available
            if prop_info.get("examples"):
                schema_example = prop_info["examples"][0]
                if isinstance(schema_example, dict):
                    example_lines.append(f"{prefix}{prop_name}:")
                    for key, value in schema_example.items():
                        if isinstance(value, str):
                            example_lines.append(f'{prefix}  {key}: "{value}"')
                        else:
                            example_lines.append(f"{prefix}  {key}: {value}")
                    continue
                elif isinstance(schema_example, str):
                    example_lines.append(f'{prefix}{prop_name}: "{schema_example}"')
                    continue
                else:
                    example_lines.append(f"{prefix}{prop_name}: {schema_example}")
                    continue

            # Use defaults if available
            default_val = prop_info.get("default")
            if default_val is not None and default_val != "__DAGSTER_UNSET_DEFAULT__":
                if isinstance(default_val, str):
                    example_lines.append(f'{prefix}{prop_name}: "{default_val}"')
                elif isinstance(default_val, bool):
                    example_lines.append(f"{prefix}{prop_name}: {str(default_val).lower()}")
                else:
                    example_lines.append(f"{prefix}{prop_name}: {default_val}")
                continue

            # Generate based on type
            if yaml_type == "string":
                # Generate contextual string examples
                contextual_examples = {
                    "project": "my_dbt_project",
                    "path": "scripts/data_pipeline.py",
                    "name": "my_component",
                    "filename": "transform.py",
                    "asset_key": "processed_data",
                    "description": "Processes raw data into clean format",
                    "target": "prod",
                    "profile": "analytics",
                    "project_dir": "./dbt",
                    "select": "tag:daily",
                    "exclude": "tag:deprecated",
                    "type": "hourly",
                    "start_date": "2024-01-01",
                    "end_date": "2024-12-31",
                    "timezone": "UTC",
                    "automation_condition": "eager",
                    "code_version": "v1.2.0",
                    "group_name": "analytics",
                    "connection_string": "postgresql://user:pass@host:5432/db",
                }
                example_value = contextual_examples.get(prop_name, "example_value")
                example_lines.append(f'{prefix}{prop_name}: "{example_value}"')

            elif yaml_type == "integer":
                contextual_integers = {
                    "minute_offset": 0,
                    "port": 5432,
                    "timeout": 300,
                    "retries": 3,
                    "batch_size": 1000,
                }
                example_value = contextual_integers.get(prop_name, 42)
                example_lines.append(f"{prefix}{prop_name}: {example_value}")

            elif yaml_type == "number":
                example_lines.append(f"{prefix}{prop_name}: 3.14")

            elif yaml_type == "boolean":
                contextual_bools = {
                    "enable_asset_checks": True,
                    "enable_code_references": True,
                    "skippable": False,
                    "blocking": False,
                    "prepare_if_dev": True,
                }
                example_value = contextual_bools.get(prop_name, True)
                example_lines.append(f"{prefix}{prop_name}: {str(example_value).lower()}")

            elif yaml_type == "array":
                example_lines.append(f"{prefix}{prop_name}:")
                if (
                    isinstance(example_obj, list)
                    and example_obj
                    and isinstance(example_obj[0], dict)
                ):
                    # Array of objects - show one complete example object
                    example_lines.append(f"{prefix}  -")
                    nested_props = example_obj[0].get("properties", {})
                    nested_required = set(example_obj[0].get("required", []))

                    # Recursively generate all properties for the array item
                    nested_examples = _generate_full_example(
                        nested_props, nested_required, indent + 2
                    )
                    for line in nested_examples:
                        # Adjust indentation for array item
                        if line.strip():  # Skip empty lines
                            example_lines.append(f"  {line}")
                else:
                    # Array of primitives - show contextual examples
                    contextual_arrays = {
                        "deps": ["upstream_table", "config_data"],
                        "owners": ["team_analytics", "john_doe"],
                        "tags": ["daily", "important"],
                        "kinds": ["table", "view"],
                        "args": ["--verbose", "--batch-size=1000"],
                    }
                    if prop_name in contextual_arrays:
                        for item in contextual_arrays[prop_name]:
                            example_lines.append(f'{prefix}  - "{item}"')
                    else:
                        example_lines.append(f'{prefix}  - "example_item"')

            elif yaml_type == "object":
                example_lines.append(f"{prefix}{prop_name}:")
                if isinstance(example_obj, dict) and "properties" in example_obj:
                    # Recursively generate all nested properties
                    nested_props = example_obj["properties"]
                    nested_required = set(example_obj.get("required", []))
                    nested_examples = _generate_full_example(
                        nested_props, nested_required, indent + 1
                    )
                    example_lines.extend(nested_examples)
                else:
                    # Generic object example
                    contextual_objects = {
                        "tags": {"team": "analytics", "priority": "high"},
                        "metadata": {"source": "api", "format": "json"},
                    }
                    if prop_name in contextual_objects:
                        for key, value in contextual_objects[prop_name].items():
                            if isinstance(value, str):
                                example_lines.append(f'{prefix}  {key}: "{value}"')
                            else:
                                example_lines.append(f"{prefix}  {key}: {value}")
                    else:
                        example_lines.append(f'{prefix}  key: "value"')

            else:
                example_lines.append(f'{prefix}{prop_name}: "example_value"')

        return example_lines

    # Generate complete example with all properties
    example_lines = _generate_full_example(properties, required_props)
    lines.extend(example_lines)

    return "\n".join(lines)
