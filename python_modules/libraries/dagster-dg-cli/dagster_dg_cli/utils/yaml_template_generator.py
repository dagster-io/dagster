"""Enhanced YAML template generator for component definitions.

This module provides functionality to generate comprehensive YAML templates
with schema documentation and example values for Dagster components.
"""

from typing import Any


def _get_field_description(field_schema: dict[str, Any]) -> str:
    """Extract field description from schema."""
    return field_schema.get("description", "")


def _get_example_value(field_schema: dict[str, Any]) -> Any:
    """Generate example values based on schema."""
    # Use schema-defined examples if available
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
        return [_get_example_value(item_schema)]
    elif field_type == "object":
        properties = field_schema.get("properties", {})
        return {
            prop_name: _get_example_value(prop_schema)
            for prop_name, prop_schema in properties.items()
        }

    return f"<{field_type or 'unknown'}>"


def _generate_schema_section(schema: dict[str, Any]) -> str:
    """Generate the schema documentation section with comments."""
    lines = []
    lines.append("# Template with instructions")
    lines.append("type: <string>  # Optional")

    if "properties" in schema:
        lines.append("attributes:  # Optional: Attributes details")

        properties = schema["properties"]
        required_fields = set(schema.get("required", []))

        for field_name, field_schema in properties.items():
            _add_field_lines(lines, field_name, field_schema, required_fields, indent="  ")

    return "\n".join(lines)


def _generate_example_section(component_type: str, schema: dict[str, Any]) -> str:
    """Generate the example values section."""
    lines = []
    lines.append("# EXAMPLE VALUES:")
    lines.append(f'type: "{component_type}"')

    if "properties" in schema:
        lines.append("attributes:")

        properties = schema["properties"]
        for field_name, field_schema in properties.items():
            example_value = _get_example_value(field_schema)
            _add_example_field_lines(lines, field_name, example_value, indent="  ")

    return "\n".join(lines)


def _add_field_lines(
    lines: list[str],
    field_name: str,
    field_schema: dict[str, Any],
    required_fields: set[str],
    indent: str = "",
) -> None:
    """Add schema field lines with appropriate formatting and comments."""
    is_required = field_name in required_fields
    required_text = "Required" if is_required else "Optional"
    description = _get_field_description(field_schema)

    field_type = field_schema.get("type", "unknown")

    if field_type == "object":
        properties = field_schema.get("properties", {})
        if properties:
            lines.append(f"{indent}{field_name}:  # {required_text}: {description}")
            sub_required = set(field_schema.get("required", []))
            for sub_field_name, sub_field_schema in properties.items():
                _add_field_lines(
                    lines, sub_field_name, sub_field_schema, sub_required, indent + "  "
                )
        else:
            lines.append(f"{indent}{field_name}:  # {required_text}: {description}")

    elif field_type == "array":
        lines.append(
            f"{indent}{field_name}:  # {required_text}: List of {field_schema.get('items', {}).get('type', 'item')} items"
        )
        item_schema = field_schema.get("items", {})
        if item_schema.get("type") == "object" and item_schema.get("properties"):
            lines.append(f"{indent}  - # List item properties:")
            item_required = set(item_schema.get("required", []))
            for item_field_name, item_field_schema in item_schema["properties"].items():
                _add_field_lines(
                    lines, item_field_name, item_field_schema, item_required, indent + "    "
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


def generate_comprehensive_defs_yaml_template(component_type: str, schema: dict[str, Any]) -> str:
    """Generate comprehensive YAML template with schema documentation and examples.

    Args:
        component_type: The component type identifier
        schema: The JSON schema for the component

    Returns:
        A comprehensive YAML template string with documentation and examples
    """
    if not schema:
        # Fallback for components without schema
        return f"""# Template with instructions
type: <string>  # Optional
attributes:  # Optional: Component attributes

# EXAMPLE VALUES:
type: "{component_type}"
attributes: {{}}"""

    schema_section = _generate_schema_section(schema)
    example_section = _generate_example_section(component_type, schema)

    return f"{schema_section}\n\n{example_section}"
