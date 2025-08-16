import pytest
from dagster_dg_core.yaml_template.converter import YamlTemplate


class TestBasicTypes:
    def test_simple_string_property(self):
        schema = {"type": "object", "properties": {"name": {"type": "string"}}}
        result = YamlTemplate.from_json_schema(schema).to_string()
        expected = (
            "# Template with instructions\n"
            "name: <string>  # Optional\n"
            "\n"
            "# EXAMPLE VALUES:\n"
            'name: "example_string"'
        )
        assert result == expected

    def test_required_string_property(self):
        schema = {
            "type": "object",
            "required": ["name"],
            "properties": {"name": {"type": "string"}},
        }
        result = YamlTemplate.from_json_schema(schema).to_string()
        expected = (
            "# Template with instructions\n"
            "name: <string>  # Required\n"
            "\n"
            "# EXAMPLE VALUES:\n"
            'name: "example_string"'
        )
        assert result == expected

    def test_integer_property(self):
        schema = {"type": "object", "properties": {"age": {"type": "integer"}}}
        result = YamlTemplate.from_json_schema(schema).to_string()
        expected = (
            "# Template with instructions\nage: <integer>  # Optional\n\n# EXAMPLE VALUES:\nage: 42"
        )
        assert result == expected

    def test_number_property(self):
        schema = {"type": "object", "properties": {"score": {"type": "number"}}}
        result = YamlTemplate.from_json_schema(schema).to_string()
        expected = (
            "# Template with instructions\n"
            "score: <number>  # Optional\n"
            "\n"
            "# EXAMPLE VALUES:\n"
            "score: 3.14"
        )
        assert result == expected

    def test_boolean_property(self):
        schema = {"type": "object", "properties": {"active": {"type": "boolean"}}}
        result = YamlTemplate.from_json_schema(schema).to_string()
        expected = (
            "# Template with instructions\n"
            "active: <boolean>  # Optional\n"
            "\n"
            "# EXAMPLE VALUES:\n"
            "active: true"
        )
        assert result == expected


class TestConstraints:
    def test_string_with_min_length(self):
        schema = {
            "type": "object",
            "required": ["name"],
            "properties": {"name": {"type": "string", "minLength": 3}},
        }
        result = YamlTemplate.from_json_schema(schema).to_string()
        expected = (
            "# Template with instructions\n"
            "name: <string>  # Required: Minimum length 3\n"
            "\n"
            "# EXAMPLE VALUES:\n"
            'name: "example_string"'
        )
        assert result == expected

    def test_string_with_max_length(self):
        schema = {"type": "object", "properties": {"code": {"type": "string", "maxLength": 10}}}
        result = YamlTemplate.from_json_schema(schema).to_string()
        expected = (
            "# Template with instructions\n"
            "code: <string>  # Optional: Maximum length 10\n"
            "\n"
            "# EXAMPLE VALUES:\n"
            'code: "example"'
        )
        assert result == expected

    def test_string_with_format(self):
        schema = {"type": "object", "properties": {"email": {"type": "string", "format": "email"}}}
        result = YamlTemplate.from_json_schema(schema).to_string()
        expected = (
            "# Template with instructions\n"
            "email: <string>  # Optional: Valid email format\n"
            "\n"
            "# EXAMPLE VALUES:\n"
            'email: "user@example.com"'
        )
        assert result == expected

    def test_integer_with_minimum(self):
        schema = {"type": "object", "properties": {"age": {"type": "integer", "minimum": 0}}}
        result = YamlTemplate.from_json_schema(schema).to_string()
        expected = (
            "# Template with instructions\n"
            "age: <integer>  # Optional: Must be >= 0\n"
            "\n"
            "# EXAMPLE VALUES:\n"
            "age: 42"
        )
        assert result == expected

    def test_integer_with_maximum(self):
        schema = {"type": "object", "properties": {"priority": {"type": "integer", "maximum": 10}}}
        result = YamlTemplate.from_json_schema(schema).to_string()
        expected = (
            "# Template with instructions\n"
            "priority: <integer>  # Optional: Must be <= 10\n"
            "\n"
            "# EXAMPLE VALUES:\n"
            "priority: 5"
        )
        assert result == expected

    def test_number_with_minimum_and_maximum(self):
        schema = {
            "type": "object",
            "properties": {"rating": {"type": "number", "minimum": 0.0, "maximum": 5.0}},
        }
        result = YamlTemplate.from_json_schema(schema).to_string()
        expected = (
            "# Template with instructions\n"
            "rating: <number>  # Optional: Must be >= 0.0 and <= 5.0\n"
            "\n"
            "# EXAMPLE VALUES:\n"
            "rating: 2.5"
        )
        assert result == expected

    def test_string_with_pattern(self):
        schema = {
            "type": "object",
            "properties": {"code": {"type": "string", "pattern": "^[A-Z]{3}-\\d{3}$"}},
        }
        result = YamlTemplate.from_json_schema(schema).to_string()
        expected = (
            "# Template with instructions\n"
            "code: <string>  # Optional: Must match pattern: ^[A-Z]{3}-\\d{3}$\n"
            "\n"
            "# EXAMPLE VALUES:\n"
            'code: "pattern_match"'
        )
        assert result == expected


class TestArrays:
    def test_simple_array(self):
        schema = {
            "type": "object",
            "properties": {"tags": {"type": "array", "items": {"type": "string"}}},
        }
        result = YamlTemplate.from_json_schema(schema).to_string()
        expected = (
            "# Template with instructions\n"
            "tags:  # Optional: List of string items\n"
            "  - <string>\n"
            "\n"
            "# EXAMPLE VALUES:\n"
            "tags:\n"
            '  - "example_item_1"\n'
            '  - "example_item_2"'
        )
        assert result == expected

    def test_required_array(self):
        schema = {
            "type": "object",
            "required": ["roles"],
            "properties": {"roles": {"type": "array", "items": {"type": "string"}}},
        }
        result = YamlTemplate.from_json_schema(schema).to_string()
        expected = (
            "# Template with instructions\n"
            "roles:  # Required: List of string items\n"
            "  - <string>\n"
            "\n"
            "# EXAMPLE VALUES:\n"
            "roles:\n"
            '  - "admin"\n'
            '  - "developer"'
        )
        assert result == expected

    def test_array_with_min_items(self):
        schema = {
            "type": "object",
            "properties": {"items": {"type": "array", "items": {"type": "string"}, "minItems": 2}},
        }
        result = YamlTemplate.from_json_schema(schema).to_string()
        expected = (
            "# Template with instructions\n"
            "items:  # Optional: List of string items, minimum 2 items\n"
            "  - <string>\n"
            "\n"
            "# EXAMPLE VALUES:\n"
            "items:\n"
            '  - "example_item_1"\n'
            '  - "example_item_2"'
        )
        assert result == expected

    def test_array_with_max_items(self):
        schema = {
            "type": "object",
            "properties": {"items": {"type": "array", "items": {"type": "integer"}, "maxItems": 3}},
        }
        result = YamlTemplate.from_json_schema(schema).to_string()
        expected = (
            "# Template with instructions\n"
            "items:  # Optional: List of integer items, maximum 3 items\n"
            "  - <integer>\n"
            "\n"
            "# EXAMPLE VALUES:\n"
            "items:\n"
            "  - 42\n"
            "  - 42"
        )
        assert result == expected


class TestNestedObjects:
    def test_nested_object(self):
        schema = {
            "type": "object",
            "properties": {
                "address": {
                    "type": "object",
                    "properties": {"street": {"type": "string"}, "city": {"type": "string"}},
                }
            },
        }
        result = YamlTemplate.from_json_schema(schema).to_string()
        expected = (
            "# Template with instructions\n"
            "address:  # Optional: Address details\n"
            "  street: <string>  # Optional\n"
            "  city: <string>  # Optional\n"
            "\n"
            "# EXAMPLE VALUES:\n"
            "address:\n"
            '  street: "example_string"\n'
            '  city: "example_string"'
        )
        assert result == expected

    def test_nested_object_with_required_fields(self):
        schema = {
            "type": "object",
            "required": ["user"],
            "properties": {
                "user": {
                    "type": "object",
                    "required": ["name"],
                    "properties": {
                        "name": {"type": "string"},
                        "email": {"type": "string", "format": "email"},
                    },
                }
            },
        }
        result = YamlTemplate.from_json_schema(schema).to_string()
        expected = (
            "# Template with instructions\n"
            "user:  # Required: User details\n"
            "  name: <string>  # Required\n"
            "  email: <string>  # Optional: Valid email format\n"
            "\n"
            "# EXAMPLE VALUES:\n"
            "user:\n"
            '  name: "example_string"\n'
            '  email: "user@example.com"'
        )
        assert result == expected


class TestComplexScenarios:
    def test_user_profile_example_from_spec(self):
        schema = {
            "type": "object",
            "required": ["name", "age", "roles"],
            "properties": {
                "name": {"type": "string", "minLength": 1},
                "age": {"type": "integer", "minimum": 0},
                "email": {"type": "string", "format": "email"},
                "roles": {"type": "array", "items": {"type": "string"}},
                "address": {
                    "type": "object",
                    "properties": {
                        "street": {"type": "string"},
                        "city": {"type": "string"},
                        "zip": {"type": "string"},
                    },
                },
            },
        }
        result = YamlTemplate.from_json_schema(schema).to_string()
        expected = (
            "# Template with instructions\n"
            "name: <string>  # Required: Minimum length 1\n"
            "age: <integer>  # Required: Must be >= 0\n"
            "email: <string>  # Optional: Valid email format\n"
            "roles:  # Required: List of string items\n"
            "  - <string>\n"
            "address:  # Optional: Address details\n"
            "  street: <string>  # Optional\n"
            "  city: <string>  # Optional\n"
            "  zip: <string>  # Optional\n"
            "\n"
            "# EXAMPLE VALUES:\n"
            'name: "example_string"\n'
            "age: 42\n"
            'email: "user@example.com"\n'
            "roles:\n"
            '  - "admin"\n'
            '  - "developer"\n'
            "address:\n"
            '  street: "example_string"\n'
            '  city: "example_string"\n'
            '  zip: "example_string"'
        )
        assert result == expected

    def test_array_of_objects(self):
        schema = {
            "type": "object",
            "properties": {
                "employees": {
                    "type": "array",
                    "items": {
                        "type": "object",
                        "required": ["name"],
                        "properties": {
                            "name": {"type": "string"},
                            "department": {"type": "string"},
                        },
                    },
                }
            },
        }
        result = YamlTemplate.from_json_schema(schema).to_string()
        expected = (
            "# Template with instructions\n"
            "employees:  # Optional: List of object items\n"
            "  - name: <string>  # Required\n"
            "    department: <string>  # Optional\n"
            "\n"
            "# EXAMPLE VALUES:\n"
            "employees:\n"
            '  - name: "example_string"\n'
            '    department: "example_string"\n'
            '  - name: "example_string"\n'
            '    department: "example_string"'
        )
        assert result == expected

    def test_empty_schema(self):
        schema = {}
        result = YamlTemplate.from_json_schema(schema).to_string()
        expected = (
            "# Template with instructions\n"
            "# No properties defined\n"
            "\n"
            "# EXAMPLE VALUES:\n"
            "# No example values available"
        )
        assert result == expected

    def test_schema_with_no_properties(self):
        schema = {"type": "object"}
        result = YamlTemplate.from_json_schema(schema).to_string()
        expected = (
            "# Template with instructions\n"
            "# No properties defined\n"
            "\n"
            "# EXAMPLE VALUES:\n"
            "# No example values available"
        )
        assert result == expected


class TestErrorHandling:
    def test_unsupported_type(self):
        schema = {"type": "object", "properties": {"unknown": {"type": "unknown_type"}}}
        result = YamlTemplate.from_json_schema(schema).to_string()
        expected = (
            "# Template with instructions\n"
            "unknown: <unknown_type>  # Optional\n"
            "\n"
            "# EXAMPLE VALUES:\n"
            'unknown: "<unknown_type_value>"'
        )
        assert result == expected

    def test_invalid_schema_structure(self):
        schema = "not a dict"
        with pytest.raises(TypeError, match="Schema must be a dictionary"):
            YamlTemplate.from_json_schema(schema)

    def test_none_schema(self):
        with pytest.raises(TypeError, match="Schema must be a dictionary"):
            YamlTemplate.from_json_schema(None)


class TestDescriptions:
    def test_property_with_description(self):
        schema = {
            "type": "object",
            "properties": {"name": {"type": "string", "description": "The user's full name"}},
        }
        result = YamlTemplate.from_json_schema(schema).to_string()
        expected = (
            "# Template with instructions\n"
            "name: <string>  # Optional: The user's full name\n"
            "\n"
            "# EXAMPLE VALUES:\n"
            'name: "example_string"'
        )
        assert result == expected


class TestYamlTemplateClass:
    def test_from_json_schema_factory_method(self):
        schema = {
            "type": "object",
            "required": ["name"],
            "properties": {"name": {"type": "string"}},
        }
        template = YamlTemplate.from_json_schema(schema)
        assert isinstance(template, YamlTemplate)

    def test_str_method(self):
        schema = {"type": "object", "properties": {"name": {"type": "string"}}}
        template = YamlTemplate.from_json_schema(schema)
        result = str(template)
        expected = (
            "# Template with instructions\n"
            "name: <string>  # Optional\n"
            "\n"
            "# EXAMPLE VALUES:\n"
            'name: "example_string"'
        )
        assert result == expected

    def test_to_string_method(self):
        schema = {"type": "object", "properties": {"name": {"type": "string"}}}
        template = YamlTemplate.from_json_schema(schema)
        result = template.to_string()
        expected = (
            "# Template with instructions\n"
            "name: <string>  # Optional\n"
            "\n"
            "# EXAMPLE VALUES:\n"
            'name: "example_string"'
        )
        assert result == expected

    def test_object_property_with_description(self):
        schema = {
            "type": "object",
            "properties": {
                "address": {
                    "type": "object",
                    "description": "User's home address",
                    "properties": {"street": {"type": "string"}},
                }
            },
        }
        result = YamlTemplate.from_json_schema(schema).to_string()
        expected = (
            "# Template with instructions\n"
            "address:  # Optional: User's home address\n"
            "  street: <string>  # Optional\n"
            "\n"
            "# EXAMPLE VALUES:\n"
            "address:\n"
            '  street: "example_string"'
        )
        assert result == expected


class TestAnyOfSchemas:
    def test_anyof_string_or_null(self):
        """Test anyOf schema with string or null types."""
        schema = {
            "type": "object",
            "properties": {
                "project": {
                    "anyOf": [{"type": "string"}, {"type": "null"}],
                    "description": "The path to the dbt project",
                }
            },
        }
        result = YamlTemplate.from_json_schema(schema).to_string()
        expected = (
            "# Template with instructions\n"
            "project: <string>  # Optional: The path to the dbt project\n"
            "\n"
            "# EXAMPLE VALUES:\n"
            'project: "example_string"'
        )
        assert result == expected

    def test_anyof_object_or_string(self):
        """Test anyOf schema with object or string types."""
        schema = {
            "type": "object",
            "properties": {
                "config": {
                    "anyOf": [
                        {
                            "type": "object",
                            "properties": {"host": {"type": "string"}, "port": {"type": "integer"}},
                        },
                        {"type": "string"},
                    ],
                    "description": "Configuration settings",
                }
            },
        }
        result = YamlTemplate.from_json_schema(schema).to_string()
        expected = (
            "# Template with instructions\n"
            "config:  # Optional: Configuration settings\n"
            "  host: <string>  # Optional\n"
            "  port: <integer>  # Optional\n"
            "\n"
            "# EXAMPLE VALUES:\n"
            "config:\n"
            '  host: "example_string"\n'
            "  port: 42"
        )
        assert result == expected

    def test_anyof_array_or_string(self):
        """Test anyOf schema with array or string types."""
        schema = {
            "type": "object",
            "properties": {
                "deps": {
                    "anyOf": [
                        {"items": {"type": "string"}, "type": "array"},
                        {"type": "string"},
                        {"type": "null"},
                    ],
                    "description": "Asset dependencies",
                }
            },
        }
        result = YamlTemplate.from_json_schema(schema).to_string()
        expected = (
            "# Template with instructions\n"
            "deps:  # Optional: Asset dependencies\n"
            "  - <string>\n"
            "\n"
            "# EXAMPLE VALUES:\n"
            "deps:\n"
            '  - "example_item_1"\n'
            '  - "example_item_2"'
        )
        assert result == expected

    def test_anyof_all_null_types(self):
        """Test anyOf schema with only null types (edge case)."""
        schema = {
            "type": "object",
            "properties": {
                "nothing": {
                    "anyOf": [{"type": "null"}, {"type": "null"}],
                    "description": "Always null",
                }
            },
        }
        result = YamlTemplate.from_json_schema(schema).to_string()
        expected = (
            "# Template with instructions\n"
            "nothing: <null>  # Optional: Always null\n"
            "\n"
            "# EXAMPLE VALUES:\n"
            "nothing: null"
        )
        assert result == expected

    def test_anyof_with_required_field(self):
        """Test anyOf schema with required field."""
        schema = {
            "type": "object",
            "required": ["project"],
            "properties": {
                "project": {
                    "anyOf": [
                        {"type": "string"},
                        {"type": "object", "properties": {"path": {"type": "string"}}},
                    ],
                    "description": "Project configuration",
                }
            },
        }
        result = YamlTemplate.from_json_schema(schema).to_string()
        expected = (
            "# Template with instructions\n"
            "project: <string>  # Required: Project configuration\n"
            "\n"
            "# EXAMPLE VALUES:\n"
            'project: "example_string"'
        )
        assert result == expected

    def test_anyof_nested_in_object(self):
        """Test anyOf schema nested within object properties."""
        schema = {
            "type": "object",
            "properties": {
                "metadata": {
                    "type": "object",
                    "properties": {
                        "value": {
                            "anyOf": [{"type": "string"}, {"type": "integer"}, {"type": "null"}],
                            "description": "Flexible metadata value",
                        }
                    },
                }
            },
        }
        result = YamlTemplate.from_json_schema(schema).to_string()
        expected = (
            "# Template with instructions\n"
            "metadata:  # Optional: Metadata details\n"
            "  value: <string>  # Optional: Flexible metadata value\n"
            "\n"
            "# EXAMPLE VALUES:\n"
            "metadata:\n"
            '  value: "example_string"'
        )
        assert result == expected


class TestRefSchemas:
    def test_simple_ref(self):
        """Test simple $ref resolution."""
        schema = {
            "type": "object",
            "$defs": {
                "PersonModel": {
                    "type": "object",
                    "properties": {"name": {"type": "string"}, "age": {"type": "integer"}},
                    "required": ["name"],
                }
            },
            "properties": {"person": {"$ref": "#/$defs/PersonModel"}},
        }
        result = YamlTemplate.from_json_schema(schema).to_string()
        expected = (
            "# Template with instructions\n"
            "person:  # Optional: Person details\n"
            "  name: <string>  # Required\n"
            "  age: <integer>  # Optional\n"
            "\n"
            "# EXAMPLE VALUES:\n"
            "person:\n"
            '  name: "example_string"\n'
            "  age: 42"
        )
        assert result == expected

    def test_ref_with_description(self):
        """Test $ref with description override."""
        schema = {
            "type": "object",
            "$defs": {
                "ConfigModel": {"type": "object", "properties": {"host": {"type": "string"}}}
            },
            "properties": {
                "config": {
                    "$ref": "#/$defs/ConfigModel",
                    "description": "Custom configuration settings",
                }
            },
        }
        result = YamlTemplate.from_json_schema(schema).to_string()
        expected = (
            "# Template with instructions\n"
            "config:  # Optional: Custom configuration settings\n"
            "  host: <string>  # Optional\n"
            "\n"
            "# EXAMPLE VALUES:\n"
            "config:\n"
            '  host: "example_string"'
        )
        assert result == expected

    def test_ref_in_anyof(self):
        """Test $ref within anyOf schema."""
        schema = {
            "type": "object",
            "$defs": {
                "DatabaseConfig": {
                    "type": "object",
                    "properties": {"url": {"type": "string"}, "port": {"type": "integer"}},
                }
            },
            "properties": {
                "config": {
                    "anyOf": [
                        {"$ref": "#/$defs/DatabaseConfig"},
                        {"type": "string"},
                        {"type": "null"},
                    ],
                    "description": "Database configuration",
                }
            },
        }
        result = YamlTemplate.from_json_schema(schema).to_string()
        expected = (
            "# Template with instructions\n"
            "config:  # Optional: Database configuration\n"
            "  url: <string>  # Optional\n"
            "  port: <integer>  # Optional\n"
            "\n"
            "# EXAMPLE VALUES:\n"
            "config:\n"
            '  url: "example_string"\n'
            "  port: 42"
        )
        assert result == expected

    def test_additional_properties_object(self):
        """Test object with additionalProperties generates example key-value."""
        schema = {
            "type": "object",
            "properties": {
                "tags": {"type": "object", "additionalProperties": True},
                "metadata": {"type": "object", "additionalProperties": True},
            },
        }
        result = YamlTemplate.from_json_schema(schema).to_string()
        expected = (
            "# Template with instructions\n"
            "tags:  # Optional: Tags details\n"
            "metadata:  # Optional: Metadata details\n"
            "\n"
            "# EXAMPLE VALUES:\n"
            "tags:\n"
            '  key: "value"\n'
            "metadata:\n"
            '  example_key: "example_value"'
        )
        assert result == expected
