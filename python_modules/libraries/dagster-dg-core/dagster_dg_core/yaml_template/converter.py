from typing import Any, Optional

from dagster_dg_core.yaml_template.template_format import (
    clean_description,
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
        self.definitions = schema.get("$defs", {})

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

    def _resolve_ref(
        self, ref_path: str, local_definitions: Optional[dict[str, Any]] = None
    ) -> dict[str, Any]:
        """Resolve a $ref path to its definition."""
        if ref_path.startswith("#/$defs/"):
            def_name = ref_path[8:]  # Remove "#/$defs/" prefix
            # First check local definitions, then fall back to global definitions
            if local_definitions and def_name in local_definitions:
                return local_definitions[def_name]
            return self.definitions.get(def_name, {})
        # For now, only handle $defs references
        return {}

    def _generate_property_template_lines(
        self,
        prop_name: str,
        prop_schema: dict[str, Any],
        indent_level: int,
        local_definitions: Optional[dict[str, Any]] = None,
    ) -> list[str]:
        """Generate template lines for a single property."""
        indent = "  " * indent_level

        # Handle $ref schemas
        if "$ref" in prop_schema:
            ref_schema = self._resolve_ref(prop_schema["$ref"], local_definitions)
            if ref_schema:
                # Merge any properties from the original schema (like description)
                merged_schema = {**ref_schema}
                for key in ["description", "title", "default"]:
                    if key in prop_schema:
                        merged_schema[key] = prop_schema[key]
                return self._generate_property_template_lines(
                    prop_name, merged_schema, indent_level, local_definitions
                )

        # Handle anyOf schemas - use the first non-null type for template generation
        if "anyOf" in prop_schema:
            for any_schema in prop_schema["anyOf"]:
                # Handle $ref within anyOf
                resolved_schema = any_schema
                if "$ref" in any_schema:
                    ref_schema = self._resolve_ref(any_schema["$ref"], local_definitions)
                    if ref_schema:
                        resolved_schema = ref_schema

                if resolved_schema.get("type") != "null":
                    # Use the description and title from the original schema if available
                    merged_schema = {**resolved_schema}
                    if "description" in prop_schema:
                        merged_schema["description"] = prop_schema["description"]
                    if "title" in prop_schema:
                        merged_schema["title"] = prop_schema["title"]
                    return self._generate_property_template_lines(
                        prop_name, merged_schema, indent_level, local_definitions
                    )
            # If all are null, treat as null type
            prop_type = "null"
        else:
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
            comment_parts.append(clean_description(prop_schema["description"]))
        elif prop_type == "object":
            comment_parts.append(get_object_description(prop_name, prop_schema))
        elif prop_type == "array":
            items_schema = prop_schema.get("items", {})

            # Handle $ref in array items for description
            resolved_items_schema = items_schema
            if "$ref" in items_schema:
                ref_schema = self._resolve_ref(items_schema["$ref"], local_definitions)
                if ref_schema:
                    resolved_items_schema = ref_schema

            array_desc = get_array_description(resolved_items_schema)
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

            # Merge local definitions from this object schema with parent local definitions
            nested_local_definitions = {}
            if local_definitions:
                nested_local_definitions.update(local_definitions)
            if "$defs" in prop_schema:
                nested_local_definitions.update(prop_schema["$defs"])

            for nested_name, nested_schema in nested_properties.items():
                # Temporarily update required fields for nested processing
                old_required = self.required_fields
                self.required_fields = nested_required

                nested_lines = self._generate_property_template_lines(
                    nested_name, nested_schema, indent_level + 1, nested_local_definitions
                )
                lines.extend(nested_lines)

                # Restore original required fields
                self.required_fields = old_required

        elif prop_type == "array":
            lines.append(f"{indent}{prop_name}:{comment}")
            items_schema = prop_schema.get("items", {})

            # Handle $ref in array items
            if "$ref" in items_schema:
                ref_schema = self._resolve_ref(items_schema["$ref"], local_definitions)
                if ref_schema:
                    items_schema = ref_schema

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
                        nested_name, nested_schema, indent_level + 1, local_definitions
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
                # Array of primitives - use <type> format for clarity
                type_display = f"<{items_type}>" if items_type != "unknown" else items_type
                lines.append(f"{indent}  - {type_display}")

        else:
            # Primitive type - use <type> format for clarity
            type_display = f"<{prop_type}>" if prop_type != "unknown" else prop_type
            lines.append(f"{indent}{prop_name}: {type_display}{comment}")

        return lines

    def _generate_example_value(
        self,
        prop_schema: dict[str, Any],
        property_name: Optional[str] = None,
        is_array_item: bool = False,
        local_definitions: Optional[dict[str, Any]] = None,
    ) -> Any:
        """Generate an example value for a property based on its schema."""
        # Handle $ref schemas
        if "$ref" in prop_schema:
            ref_schema = self._resolve_ref(prop_schema["$ref"], local_definitions)
            if ref_schema:
                return self._generate_example_value(
                    ref_schema, property_name, is_array_item, local_definitions
                )

        # Handle anyOf schemas - use the first non-null type
        if "anyOf" in prop_schema:
            for any_schema in prop_schema["anyOf"]:
                # Handle $ref within anyOf
                resolved_schema = any_schema
                if "$ref" in any_schema:
                    ref_schema = self._resolve_ref(any_schema["$ref"], local_definitions)
                    if ref_schema:
                        resolved_schema = ref_schema

                if resolved_schema.get("type") != "null":
                    return self._generate_example_value(
                        resolved_schema, property_name, is_array_item, local_definitions
                    )
            # If all are null, return null
            return None

        prop_type = prop_schema.get("type", "unknown")

        if prop_type == "object":
            example_obj = {}
            nested_properties = prop_schema.get("properties", {})

            # Merge local definitions from this object schema with parent local definitions
            nested_local_definitions = {}
            if local_definitions:
                nested_local_definitions.update(local_definitions)
            if "$defs" in prop_schema:
                nested_local_definitions.update(prop_schema["$defs"])

            for nested_name, nested_schema in nested_properties.items():
                # For array items or nested objects, pass the is_array_item flag and local definitions
                example_obj[nested_name] = self._generate_example_value(
                    nested_schema,
                    property_name=nested_name,
                    is_array_item=is_array_item,
                    local_definitions=nested_local_definitions,
                )

            # If no properties but additionalProperties is allowed, add an example key-value pair
            if not nested_properties and prop_schema.get("additionalProperties"):
                # Generate a contextual example based on property name
                if property_name == "tags":
                    example_obj["key"] = "value"
                elif property_name == "metadata":
                    example_obj["example_key"] = "example_value"
                else:
                    example_obj["key"] = "value"

            return example_obj

        elif prop_type == "array":
            items_schema = prop_schema.get("items", {})

            # Handle $ref in array items
            if "$ref" in items_schema:
                ref_schema = self._resolve_ref(items_schema["$ref"], local_definitions)
                if ref_schema:
                    items_schema = ref_schema

            items_type = items_schema.get("type", "unknown")

            if items_type == "object":
                # Array of objects - generate 1 example item with array item flag
                example_item = self._generate_example_value(
                    items_schema,
                    property_name=None,
                    is_array_item=True,
                    local_definitions=local_definitions,
                )
                return [example_item]
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
                    return [example_item]

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
