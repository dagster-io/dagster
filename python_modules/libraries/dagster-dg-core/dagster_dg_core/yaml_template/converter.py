from typing import Any, Optional

from dagster_dg_core.yaml_template.template_format import (
    format_dict_as_yaml,
    get_array_description,
    get_constraint_description,
    get_example_value_for_type,
    get_object_description,
)


class YamlTemplate:
    """A YAML template generated from a JSON Schema, optimized for LLM consumption."""

    def __init__(self, template_section: str, example_section: str):
        self._template_section = template_section
        self._example_section = example_section

    @staticmethod
    def from_json_schema(schema: Any) -> "YamlTemplate":
        """Create a YamlTemplate from a JSON Schema dictionary."""
        if not isinstance(schema, dict):
            raise TypeError("Schema must be a dictionary")

        converter = JsonSchemaConverter(schema)
        template_section = converter.generate_template_section()
        example_section = converter.generate_example_section()

        return YamlTemplate(template_section, example_section)

    def __str__(self) -> str:
        """Return the complete YAML template as a string."""
        return f"{self._template_section}\n\n{self._example_section}"

    def to_string(self) -> str:
        """Return the complete YAML template as a string."""
        return str(self)


class JsonSchemaConverter:
    """Converts JSON Schema to YAML template format."""

    def __init__(self, schema: dict[str, Any]):
        self.schema = schema
        self.required_fields = set(schema.get("required", []))
        self.properties = schema.get("properties", {})

    def generate_template_section(self) -> str:
        """Generate the template instructions section."""
        if not self.properties:
            return "# Template with instructions\n# No properties defined"

        lines = ["# Template with instructions"]
        for prop_name, prop_schema in self.properties.items():
            lines.extend(self._generate_property_template_lines(prop_name, prop_schema, 0))

        return "\n".join(lines)

    def generate_example_section(self) -> str:
        """Generate the example values section."""
        if not self.properties:
            return "# EXAMPLE VALUES:\n# No example values available"

        lines = ["# EXAMPLE VALUES:"]
        example_data = {}

        for prop_name, prop_schema in self.properties.items():
            example_data[prop_name] = self._generate_example_value(prop_schema, prop_name)

        example_yaml = format_dict_as_yaml(example_data, 0)
        lines.extend(example_yaml.split("\n"))

        return "\n".join(lines)

    def _generate_property_template_lines(
        self, prop_name: str, prop_schema: dict[str, Any], indent_level: int
    ) -> list[str]:
        """Generate template lines for a single property."""
        indent = "  " * indent_level
        prop_type = prop_schema.get("type", "unknown")

        # Build comment parts
        comment_parts = []

        # Required/Optional status
        if prop_name in self.required_fields:
            comment_parts.append("Required")
        else:
            comment_parts.append("Optional")

        # Add description if present
        if "description" in prop_schema:
            comment_parts.append(prop_schema["description"])
        elif prop_type == "object":
            comment_parts.append(get_object_description(prop_name, prop_schema))
        elif prop_type == "array":
            items_schema = prop_schema.get("items", {})
            array_desc = get_array_description(items_schema)
            comment_parts.append(array_desc)

        # Add constraints
        if prop_type == "array":
            # For arrays, handle minItems/maxItems directly in get_constraint_description
            constraint_desc = get_constraint_description(prop_type, prop_schema)
            if constraint_desc:
                comment_parts.append(constraint_desc)
        else:
            constraint_desc = get_constraint_description(prop_type, prop_schema)
            if constraint_desc:
                comment_parts.append(constraint_desc)

        # Build comment with proper separators
        if len(comment_parts) == 1:
            comment = f"  # {comment_parts[0]}"
        elif len(comment_parts) == 2:
            comment = f"  # {comment_parts[0]}: {comment_parts[1]}"
        else:
            # First two parts with colon, rest with commas
            comment = f"  # {comment_parts[0]}: {comment_parts[1]}"
            if len(comment_parts) > 2:
                comment += ", " + ", ".join(comment_parts[2:])

        lines = []

        if prop_type == "object":
            lines.append(f"{indent}{prop_name}:{comment}")
            nested_properties = prop_schema.get("properties", {})
            nested_required = set(prop_schema.get("required", []))

            for nested_name, nested_schema in nested_properties.items():
                # Temporarily update required fields for nested processing
                old_required = self.required_fields
                self.required_fields = nested_required

                nested_lines = self._generate_property_template_lines(
                    nested_name, nested_schema, indent_level + 1
                )
                lines.extend(nested_lines)

                # Restore original required fields
                self.required_fields = old_required

        elif prop_type == "array":
            lines.append(f"{indent}{prop_name}:{comment}")
            items_schema = prop_schema.get("items", {})
            items_type = items_schema.get("type", "unknown")

            if items_type == "object":
                # Array of objects
                nested_properties = items_schema.get("properties", {})
                nested_required = set(items_schema.get("required", []))

                # Temporarily update required fields for nested processing
                old_required = self.required_fields
                self.required_fields = nested_required

                # Generate the first property with "- " prefix, others with normal indentation
                first_property = True
                for nested_name, nested_schema in nested_properties.items():
                    nested_lines = self._generate_property_template_lines(
                        nested_name, nested_schema, indent_level + 1
                    )
                    if nested_lines and first_property:
                        # First property gets the "- " prefix
                        first_line = nested_lines[0]
                        # Extract the part after the base indent
                        base_indent_len = len(f"{indent}  ")
                        if len(first_line) > base_indent_len:
                            content_part = first_line[base_indent_len:]
                            nested_lines[0] = f"{indent}  - {content_part}"
                        first_property = False
                    elif nested_lines:
                        # Subsequent properties get normal indentation but at array item level
                        for i, line in enumerate(nested_lines):
                            base_indent_len = len(f"{indent}  ")
                            if len(line) > base_indent_len:
                                content_part = line[base_indent_len:]
                                nested_lines[i] = f"{indent}    {content_part}"
                    lines.extend(nested_lines)

                # Restore original required fields
                self.required_fields = old_required
            else:
                # Array of primitives
                lines.append(f"{indent}  - {items_type}")

        else:
            # Primitive type
            lines.append(f"{indent}{prop_name}: {prop_type}{comment}")

        return lines

    def _generate_example_value(
        self,
        prop_schema: dict[str, Any],
        property_name: Optional[str] = None,
        is_array_item: bool = False,
    ) -> Any:
        """Generate an example value for a property based on its schema."""
        prop_type = prop_schema.get("type", "unknown")

        if prop_type == "object":
            example_obj = {}
            nested_properties = prop_schema.get("properties", {})

            for nested_name, nested_schema in nested_properties.items():
                # For array items or nested objects, pass the is_array_item flag
                example_obj[nested_name] = self._generate_example_value(
                    nested_schema, property_name=nested_name, is_array_item=is_array_item
                )

            return example_obj

        elif prop_type == "array":
            items_schema = prop_schema.get("items", {})
            items_type = items_schema.get("type", "unknown")

            if items_type == "object":
                # Array of objects - generate 2 example items with array item flag
                example_item = self._generate_example_value(
                    items_schema, property_name=None, is_array_item=True
                )
                return [example_item, example_item]
            else:
                # Array of primitives - generate different example values
                format_hint = items_schema.get("format")
                if property_name == "roles":
                    return ["admin", "developer"]
                elif items_type == "string" and not format_hint:
                    return ["example_item_1", "example_item_2"]
                else:
                    example_item = get_example_value_for_type(
                        items_type,
                        format_hint=format_hint,
                        constraints=items_schema,
                        property_name=property_name,
                        is_array_item=True,
                    )
                    return [example_item, example_item]

        else:
            # Primitive type
            format_hint = prop_schema.get("format")
            return get_example_value_for_type(
                prop_type,
                format_hint=format_hint,
                constraints=prop_schema,
                property_name=property_name,
                is_array_item=is_array_item,
            )
