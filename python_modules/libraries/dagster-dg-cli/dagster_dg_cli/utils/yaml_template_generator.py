"""Enhanced YAML template generator for component definitions.

This module provides functionality to generate comprehensive YAML templates
with schema documentation and example values for Dagster components.
"""

from typing import Any, Optional


def _get_field_description(field_schema: dict[str, Any]) -> str:
    """Extract field description from schema."""
    return field_schema.get("description", "")


def _resolve_ref(ref_path: str, full_schema: dict[str, Any]) -> dict[str, Any]:
    """Resolve a $ref path to its actual schema definition."""
    if not ref_path.startswith("#/$defs/"):
        return {}

    ref_name = ref_path.replace("#/$defs/", "")
    return full_schema.get("$defs", {}).get(ref_name, {})


def _get_example_value(
    field_schema: dict[str, Any], full_schema: Optional[dict[str, Any]] = None
) -> Any:
    """Generate example values based on schema."""
    full_schema = full_schema or {}

    # Handle $ref objects
    if "$ref" in field_schema:
        ref_schema = _resolve_ref(field_schema["$ref"], full_schema)
        return _get_example_value(ref_schema, full_schema)

    # Handle anyOf schemas by preferring non-string types over string types
    # Do this BEFORE using schema examples to ensure we show the true underlying data structure
    if "anyOf" in field_schema:
        ref_options = []
        non_string_options = []
        string_options = []

        for option in field_schema["anyOf"]:
            if option.get("type") == "null":
                continue
            elif "$ref" in option:
                ref_options.append(option)
            elif option.get("type") == "string":
                string_options.append(option)
            else:
                non_string_options.append(option)

        # For union types with multiple $ref objects, use the first complex $ref option
        if len(ref_options) > 1:
            # Find the first $ref that resolves to a complex object with properties
            for ref_option in ref_options:
                ref_schema = _resolve_ref(ref_option["$ref"], full_schema)
                if ref_schema and ref_schema.get("properties"):
                    return _get_example_value(ref_schema, full_schema)
            # Fall back to first $ref if none have properties
            return _get_example_value(ref_options[0], full_schema)

        # Prefer $ref options, then non-string types, then string types
        all_options = ref_options + non_string_options + string_options
        if all_options:
            return _get_example_value(all_options[0], full_schema)

        # If all options are null, return null
        return None

    # Use schema-defined examples if available (for non-anyOf fields)
    if field_schema.get("examples"):
        return field_schema["examples"][0]

    field_type = field_schema.get("type")

    # Generic type-based examples
    if field_type == "string":
        return "example_string"
    elif field_type == "boolean":
        return True
    elif field_type == "integer":
        return 1
    elif field_type == "number":
        return 1.0
    elif field_type == "array":
        item_schema = field_schema.get("items", {})
        return [_get_example_value(item_schema, full_schema)]
    elif field_type == "object":
        properties = field_schema.get("properties", {})
        if properties:
            return {
                prop_name: _get_example_value(prop_schema, full_schema)
                for prop_name, prop_schema in properties.items()
            }
        elif field_schema.get("additionalProperties"):
            # Handle objects with additionalProperties but no specific properties
            additional_props_schema = field_schema.get("additionalProperties")
            if (
                isinstance(additional_props_schema, dict)
                and additional_props_schema.get("type") == "string"
            ):
                # Return a simple example object with string values
                return {"key": "value"}
            elif additional_props_schema is True:
                # additionalProperties: true means any properties are allowed
                return {"key": "value"}
        return {}

    return f"<{field_type or 'unknown'}>"


def _generate_schema_section(component_type: str, schema: dict[str, Any]) -> str:
    """Generate the schema documentation section as valid YAML with comments."""
    lines = []
    lines.append("# Template with instructions")
    lines.append(f"type: {component_type}  # Required")

    if "properties" in schema:
        lines.append("attributes:  # Optional: Attributes details")

        properties = schema["properties"]
        required_fields = set(schema.get("required", []))

        for field_name, field_schema in properties.items():
            _add_field_lines(lines, field_name, field_schema, required_fields, schema, indent="  ")
    else:
        lines.append("attributes:  # Optional: Attributes details")

    return "\n".join(lines)


def _generate_example_section(component_type: str, schema: dict[str, Any]) -> str:
    """Generate the example values section as valid YAML."""
    lines = []
    lines.append(f'type: "{component_type}"')

    if schema.get("properties"):
        lines.append("attributes:")

        properties = schema["properties"]
        for field_name, field_schema in properties.items():
            example_value = _get_example_value(field_schema, schema)
            _add_example_field_lines(lines, field_name, example_value, indent="  ")
    else:
        lines.append("attributes: {}")

    return "\n".join(lines)


def _generate_union_type_schema(
    lines: list[str],
    field_name: str,
    ref_options: list[dict[str, Any]],
    required_text: str,
    description: str,
    full_schema: dict[str, Any],
    indent: str = "",
) -> None:
    """Generate schema documentation for union types with multiple $ref objects."""
    lines.append(f"{indent}{field_name}:  # {required_text}: {description}")
    lines.append(f"{indent}  # Choose one of the following types:")

    for i, option in enumerate(ref_options, 1):
        ref_path = option["$ref"]
        ref_name = ref_path.split("/")[-1]
        ref_schema = _resolve_ref(ref_path, full_schema)

        if ref_schema and ref_schema.get("properties"):
            lines.append(f"{indent}  # Option {i} - {ref_name}:")
            sub_required = set(ref_schema.get("required", []))
            for sub_field_name, sub_field_schema in ref_schema["properties"].items():
                _add_field_lines(
                    lines,
                    f"# {sub_field_name}",
                    sub_field_schema,
                    sub_required,
                    full_schema,
                    indent + "  ",
                )
            lines.append(f"{indent}  #")


def _get_field_type_description(field_schema: dict[str, Any]) -> str:
    """Get a user-friendly type description for a field schema."""
    # Handle anyOf schemas
    if "anyOf" in field_schema:
        non_null_types = []
        for option in field_schema["anyOf"]:
            if option.get("type") != "null":
                if option.get("type") == "array":
                    item_type = option.get("items", {}).get("type", "item")
                    non_null_types.append(f"array of {item_type}")
                elif "$ref" in option:
                    ref_name = option["$ref"].split("/")[-1]
                    non_null_types.append(f"object ({ref_name})")
                else:
                    non_null_types.append(option.get("type", "unknown"))

        if non_null_types:
            if len(non_null_types) == 1:
                return non_null_types[0]
            else:
                return f"one of: {', '.join(non_null_types)}"

    # Handle regular type
    field_type = field_schema.get("type", "unknown")
    if field_type == "array":
        item_type = field_schema.get("items", {}).get("type", "item")
        return f"array of {item_type}"

    return field_type


def _add_field_lines(
    lines: list[str],
    field_name: str,
    field_schema: dict[str, Any],
    required_fields: set[str],
    full_schema: dict[str, Any],
    indent: str = "",
) -> None:
    """Add schema field lines with appropriate formatting and comments."""
    is_required = field_name in required_fields
    required_text = "Required" if is_required else "Optional"
    description = _get_field_description(field_schema)

    # Handle $ref objects - resolve and recurse
    if "$ref" in field_schema:
        ref_schema = _resolve_ref(field_schema["$ref"], full_schema)
        if ref_schema:
            _add_field_lines(lines, field_name, ref_schema, required_fields, full_schema, indent)
            return

    # Handle anyOf schemas - check for union types with multiple $ref objects
    if "anyOf" in field_schema:
        # Collect all $ref options (potential union type)
        ref_options = [option for option in field_schema["anyOf"] if "$ref" in option]

        # If we have multiple $ref options, treat as union type
        if len(ref_options) > 1:
            _generate_union_type_schema(
                lines, field_name, ref_options, required_text, description, full_schema, indent
            )
            return

        # Check if any anyOf option is a complex object that should be expanded (existing logic)
        complex_option = None
        for option in field_schema["anyOf"]:
            if option.get("type") == "array":
                items = option.get("items", {})
                if "$ref" in items:
                    # This is an array of complex objects - expand it
                    ref_schema = _resolve_ref(items["$ref"], full_schema)
                    if ref_schema and ref_schema.get("properties"):
                        lines.append(f"{indent}{field_name}:  # {required_text}: {description}")
                        lines.append(
                            f"{indent}  - # Array of {items['$ref'].split('/')[-1]} objects:"
                        )
                        sub_required = set(ref_schema.get("required", []))
                        for sub_field_name, sub_field_schema in ref_schema["properties"].items():
                            _add_field_lines(
                                lines,
                                sub_field_name,
                                sub_field_schema,
                                sub_required,
                                full_schema,
                                indent + "    ",
                            )
                        return
            elif "$ref" in option:
                ref_schema = _resolve_ref(option["$ref"], full_schema)
                if ref_schema and ref_schema.get("properties"):
                    complex_option = ref_schema
                    break

        if complex_option:
            # Expand the complex object option
            lines.append(f"{indent}{field_name}:  # {required_text}: {description}")
            sub_required = set(complex_option.get("required", []))
            for sub_field_name, sub_field_schema in complex_option["properties"].items():
                _add_field_lines(
                    lines,
                    sub_field_name,
                    sub_field_schema,
                    sub_required,
                    full_schema,
                    indent + "  ",
                )
        else:
            # Fall back to type description for simple anyOf
            type_desc = _get_field_type_description(field_schema)
            lines.append(f"{indent}{field_name}: <{type_desc}>  # {required_text}: {description}")
        return

    field_type = field_schema.get("type", "unknown")

    if field_type == "object":
        properties = field_schema.get("properties", {})
        if properties:
            lines.append(f"{indent}{field_name}:  # {required_text}: {description}")
            sub_required = set(field_schema.get("required", []))
            for sub_field_name, sub_field_schema in properties.items():
                _add_field_lines(
                    lines,
                    sub_field_name,
                    sub_field_schema,
                    sub_required,
                    full_schema,
                    indent + "  ",
                )
        else:
            lines.append(f"{indent}{field_name}:  # {required_text}: {description}")

    elif field_type == "array":
        item_schema = field_schema.get("items", {})

        # Handle array of complex objects via $ref
        if "$ref" in item_schema:
            ref_schema = _resolve_ref(item_schema["$ref"], full_schema)
            if ref_schema and ref_schema.get("properties"):
                lines.append(f"{indent}{field_name}:  # {required_text}: {description}")
                lines.append(
                    f"{indent}  - # Array of {item_schema['$ref'].split('/')[-1]} objects:"
                )
                sub_required = set(ref_schema.get("required", []))
                for sub_field_name, sub_field_schema in ref_schema["properties"].items():
                    _add_field_lines(
                        lines,
                        sub_field_name,
                        sub_field_schema,
                        sub_required,
                        full_schema,
                        indent + "    ",
                    )
                return

        # Handle regular arrays
        lines.append(
            f"{indent}{field_name}:  # {required_text}: List of {item_schema.get('type', 'item')} items"
        )
        if item_schema.get("type") == "object" and item_schema.get("properties"):
            lines.append(f"{indent}  - # List item properties:")
            item_required = set(item_schema.get("required", []))
            for item_field_name, item_field_schema in item_schema["properties"].items():
                _add_field_lines(
                    lines,
                    item_field_name,
                    item_field_schema,
                    item_required,
                    full_schema,
                    indent + "    ",
                )
        else:
            lines.append(f"{indent}  - <{item_schema.get('type', 'string')}>")

    else:
        lines.append(f"{indent}{field_name}: <{field_type}>  # {required_text}: {description}")


def _add_example_field_lines(
    lines: list[str], field_name: str, value: Any, indent: str = ""
) -> None:
    """Add example field lines with proper YAML formatting."""
    if isinstance(value, dict):
        lines.append(f"{indent}{field_name}:")
        for sub_key, sub_value in value.items():
            _add_example_field_lines(lines, sub_key, sub_value, indent + "  ")
    elif isinstance(value, list):
        lines.append(f"{indent}{field_name}:")
        for item in value:
            if isinstance(item, dict):
                lines.append(f"{indent}  -")
                for sub_key, sub_value in item.items():
                    _add_example_field_lines(lines, sub_key, sub_value, indent + "    ")
            else:
                lines.append(f'{indent}  - "{item}"')
    elif isinstance(value, str):
        lines.append(f'{indent}{field_name}: "{value}"')
    elif isinstance(value, bool):
        lines.append(f"{indent}{field_name}: {str(value).lower()}")
    else:
        lines.append(f"{indent}{field_name}: {value}")


def generate_defs_yaml_schema(component_type: str, schema: dict[str, Any]) -> str:
    """Generate YAML schema template with type information and documentation.

    Args:
        component_type: The component type identifier
        schema: The JSON schema for the component

    Returns:
        A YAML template string with schema documentation and type hints
    """
    if not schema:
        # Fallback for components without schema
        return f"""# Template with instructions
type: {component_type}  # Required
attributes:  # Optional: Attributes details"""

    return _generate_schema_section(component_type, schema)


def generate_defs_yaml_example_values(component_type: str, schema: dict[str, Any]) -> str:
    """Generate YAML example values with sample data.

    Args:
        component_type: The component type identifier
        schema: The JSON schema for the component

    Returns:
        A YAML string with example values and sample data
    """
    if not schema:
        # Fallback for components without schema
        return f"""type: "{component_type}"
attributes: {{}}"""

    return _generate_example_section(component_type, schema)
