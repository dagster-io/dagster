import json

from dagster_dg_cli.cli.agent_project_context.schema_utils import (
    generate_yaml_template_from_schema,
    print_simplified_schema,
)
from dagster_test.dg_utils.utils import ProxyRunner, assert_runner_result, isolated_components_venv


def test_agent_project_context_json_format():
    """Test that the command with --output=json produces valid JSON."""
    with (
        ProxyRunner.test(use_fixed_test_components=True) as runner,
        isolated_components_venv(runner),
    ):
        result = runner.invoke(
            "utils",
            "agent-project-context",
            "--output",
            "json",
        )
        assert_runner_result(result)

        # Should be valid JSON
        output_data = json.loads(result.output)
        assert "working_directory" in output_data
        assert "project_root" in output_data
        assert "components" in output_data
        assert "integrations" in output_data


def test_agent_project_context_readable_format():
    """Test that the command with --output=markdown produces readable output."""
    with (
        ProxyRunner.test(use_fixed_test_components=True) as runner,
        isolated_components_venv(runner),
    ):
        result = runner.invoke(
            "utils",
            "agent-project-context",
            "--output",
            "markdown",
        )
        assert_runner_result(result)

        # Should be readable format
        assert "## Available Project Context" in result.output


def test_agent_project_context_default_is_readable():
    """Test that the command defaults to readable format."""
    with (
        ProxyRunner.test(use_fixed_test_components=True) as runner,
        isolated_components_venv(runner),
    ):
        result = runner.invoke("utils", "agent-project-context")
        assert_runner_result(result)

        # Should be readable format
        assert "## Available Project Context" in result.output


def test_agent_project_context_xml_format():
    """Test that the command with --output=xml produces valid XML."""
    with (
        ProxyRunner.test(use_fixed_test_components=True) as runner,
        isolated_components_venv(runner),
    ):
        result = runner.invoke(
            "utils",
            "agent-project-context",
            "--output",
            "xml",
        )
        assert_runner_result(result)

        # Should be XML format
        assert "<project_context>" in result.output
        assert "</project_context>" in result.output


class TestPrintSimplifiedSchema:
    """Unit tests for the print_simplified_schema function."""

    def test_empty_schema(self, capsys):
        """Test handling of schema with no properties."""
        schema = {}
        print_simplified_schema(schema)
        captured = capsys.readouterr()

        assert "(No configuration properties defined)" in captured.out

    def test_simple_properties(self, capsys):
        """Test display of simple properties."""
        schema = {
            "properties": {
                "name": {"type": "string", "description": "Component name"},
                "count": {"type": "integer", "description": "Number of items"},
                "enabled": {"type": "boolean"},
            },
            "required": ["name"],
        }
        print_simplified_schema(schema)
        captured = capsys.readouterr()

        assert "**name** (`string`) **(required)**: Component name" in captured.out
        assert "**count** (`integer`): Number of items" in captured.out
        assert "**enabled** (`boolean`)" in captured.out

    def test_array_and_object_types(self, capsys):
        """Test display of array and object types."""
        schema = {
            "properties": {
                "tags": {
                    "type": "array",
                    "items": {"type": "string"},
                    "description": "List of tags",
                },
                "config": {
                    "type": "object",
                    "properties": {"key": {"type": "string"}},
                    "description": "Configuration object",
                },
            }
        }
        print_simplified_schema(schema)
        captured = capsys.readouterr()

        assert "**tags** (`array of string`): List of tags" in captured.out
        assert "**config** (`object`): Configuration object" in captured.out

    def test_truncates_long_descriptions(self, capsys):
        """Test that long descriptions are truncated."""
        long_desc = "A" * 100  # Longer than 80 chars
        schema = {
            "properties": {
                "field": {"type": "string", "description": long_desc},
            }
        }
        print_simplified_schema(schema)
        captured = capsys.readouterr()

        assert long_desc not in captured.out
        assert "..." in captured.out

    def test_limits_property_count(self, capsys):
        """Test that only first 8 properties are shown."""
        properties = {f"field_{i}": {"type": "string"} for i in range(12)}
        schema = {"properties": properties}

        print_simplified_schema(schema)
        captured = capsys.readouterr()

        assert "...and 4 more properties" in captured.out


class TestGenerateYamlTemplateFromSchema:
    """Unit tests for the generate_yaml_template_from_schema function."""

    def test_simple_schema(self):
        """Test generation with simple properties."""
        schema = {
            "properties": {
                "name": {"type": "string", "description": "Component name"},
                "count": {"type": "integer", "default": 1},
            },
            "required": ["name"],
        }

        template = generate_yaml_template_from_schema(schema, "TestComponent")

        assert "# Template for TestComponent" in template
        assert "name: string # string; Required; Component name" in template
        assert "count: integer # integer; Optional; Default: 1" in template

    def test_complex_schema_with_nested_objects(self):
        """Test generation with nested objects and arrays."""
        schema = {
            "properties": {
                "project": {"type": "string", "description": "dbt project path"},
                "deps": {
                    "type": "array",
                    "items": {"type": "string"},
                    "description": "Dependencies",
                },
                "config": {
                    "type": "object",
                    "properties": {
                        "target": {"type": "string", "default": "dev"},
                        "threads": {"type": "integer", "default": 4},
                    },
                },
            },
            "required": ["project"],
        }

        template = generate_yaml_template_from_schema(schema, "DbtProjectComponent")

        assert "# Template for DbtProjectComponent" in template
        assert "project:" in template
        assert "deps:" in template
        assert "config:" in template
        assert "target:" in template
        assert "threads:" in template

    def test_array_of_objects(self):
        """Test generation with array of objects."""
        schema = {
            "properties": {
                "items": {
                    "type": "array",
                    "items": {
                        "type": "object",
                        "properties": {
                            "name": {"type": "string"},
                            "value": {"type": "integer"},
                        },
                        "required": ["name"],
                    },
                }
            }
        }

        template = generate_yaml_template_from_schema(schema, "ArrayComponent")

        assert "items:" in template
        assert "  -" in template
        assert "name:" in template
        assert "value:" in template

    def test_with_examples_in_schema(self):
        """Test that schema examples are used when available."""
        schema = {
            "properties": {
                "connection_string": {
                    "type": "string",
                    "examples": ["postgresql://user:pass@localhost:5432/db"],
                },
                "timeout": {"type": "integer", "examples": [300]},
            }
        }

        template = generate_yaml_template_from_schema(schema, "SlingComponent")

        assert '"postgresql://user:pass@localhost:5432/db"' in template
        assert "300" in template

    def test_with_const_values(self):
        """Test handling of const values in schema."""
        schema = {
            "properties": {
                "type": {"type": "string", "const": "python_script"},
                "version": {"type": "string"},
            }
        }

        template = generate_yaml_template_from_schema(schema, "PythonScriptComponent")

        assert '"python_script"' in template
