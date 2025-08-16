import json
import textwrap

from dagster_dg_cli.cli.utils import _generate_defs_yaml_schema
from dagster_test.dg_utils.utils import ProxyRunner, assert_runner_result, isolated_components_venv

# ########################
# ##### COMPONENT TYPE
# ########################

_EXPECTED_INSPECT_COMPONENT_TYPE_FULL = textwrap.dedent("""
    dagster_test.components.SimplePipesScriptComponent

    Description:

    A simple asset that runs a Python script with the Pipes subprocess client.

    Because it is a pipes asset, no value is returned.

    Scaffold params schema:

    {
        "properties": {
            "asset_key": {
                "title": "Asset Key",
                "type": "string"
            },
            "filename": {
                "title": "Filename",
                "type": "string"
            }
        },
        "required": [
            "asset_key",
            "filename"
        ],
        "title": "SimplePipesScriptScaffoldParams",
        "type": "object"
    }

    Component schema:

    {
        "additionalProperties": false,
        "properties": {
            "asset_key": {
                "title": "Asset Key",
                "type": "string"
            },
            "filename": {
                "title": "Filename",
                "type": "string"
            }
        },
        "required": [
            "asset_key",
            "filename"
        ],
        "title": "SimplePipesScriptComponentModel",
        "type": "object"
    }
""").strip()


def test_utils_inspect_component_type_all_metadata_success():
    with (
        ProxyRunner.test(use_fixed_test_components=True) as runner,
        isolated_components_venv(runner),
    ):
        result = runner.invoke(
            "utils",
            "inspect-component",
            "dagster_test.components.SimplePipesScriptComponent",
        )
        assert_runner_result(result)
        assert result.output.strip().endswith(_EXPECTED_INSPECT_COMPONENT_TYPE_FULL)


def test_utils_inspect_component_type_all_metadata_empty_success():
    with (
        ProxyRunner.test(use_fixed_test_components=True) as runner,
        isolated_components_venv(runner),
    ):
        result = runner.invoke(
            "utils",
            "inspect-component",
            "dagster_test.components.AllMetadataEmptyComponent",
        )
        assert_runner_result(result)


def test_utils_inspect_component_type_flag_fields_success():
    with (
        ProxyRunner.test(use_fixed_test_components=True) as runner,
        isolated_components_venv(runner),
    ):
        result = runner.invoke(
            "utils",
            "inspect-component",
            "dagster_test.components.SimplePipesScriptComponent",
            "--description",
        )
        assert_runner_result(result)
        assert result.output.strip().endswith(
            textwrap.dedent("""
            A simple asset that runs a Python script with the Pipes subprocess client.

            Because it is a pipes asset, no value is returned.
        """).strip()
        )

        result = runner.invoke(
            "utils",
            "inspect-component",
            "dagster_test.components.SimplePipesScriptComponent",
            "--scaffold-params-schema",
        )
        assert_runner_result(result)
        assert result.output.strip().endswith(
            textwrap.dedent("""
                {
                    "properties": {
                        "asset_key": {
                            "title": "Asset Key",
                            "type": "string"
                        },
                        "filename": {
                            "title": "Filename",
                            "type": "string"
                        }
                    },
                    "required": [
                        "asset_key",
                        "filename"
                    ],
                    "title": "SimplePipesScriptScaffoldParams",
                    "type": "object"
                }
            """).strip()
        )

        result = runner.invoke(
            "utils",
            "inspect-component",
            "dagster_test.components.SimplePipesScriptComponent",
            "--component-schema",
        )
        assert_runner_result(result)
        assert result.output.strip().endswith(
            textwrap.dedent("""
                {
                    "additionalProperties": false,
                    "properties": {
                        "asset_key": {
                            "title": "Asset Key",
                            "type": "string"
                        },
                        "filename": {
                            "title": "Filename",
                            "type": "string"
                        }
                    },
                    "required": [
                        "asset_key",
                        "filename"
                    ],
                    "title": "SimplePipesScriptComponentModel",
                    "type": "object"
                }
            """).strip()
        )

        result = runner.invoke(
            "utils",
            "inspect-component",
            "dagster_test.components.SimplePipesScriptComponent",
            "--defs-yaml-schema",
        )
        assert_runner_result(result)
        # Check that the output contains the ComponentFileModel structure
        output_json = json.loads(result.output.strip())
        assert "properties" in output_json
        assert "type" in output_json["properties"]
        assert "attributes" in output_json["properties"]
        assert "template_vars_module" in output_json["properties"]
        assert "requirements" in output_json["properties"]
        assert "post_processing" in output_json["properties"]
        # Check that type is constrained to the specific component
        assert (
            output_json["properties"]["type"]["const"]
            == "dagster_test.components.SimplePipesScriptComponent"
        )


def test_utils_inspect_component_type_multiple_flags_fails() -> None:
    with (
        ProxyRunner.test(use_fixed_test_components=True) as runner,
        isolated_components_venv(runner),
    ):
        result = runner.invoke(
            "utils",
            "inspect-component",
            "dagster_test.components.SimplePipesScriptComponent",
            "--description",
            "--scaffold-params-schema",
        )
        assert_runner_result(result, exit_0=False)
        assert (
            "Only one of --description, --scaffold-params-schema, --component-schema, and --defs-yaml-schema can be specified."
            in result.output
        )


def test_utils_inspect_component_type_defs_yaml_schema_with_other_flags_fails() -> None:
    with (
        ProxyRunner.test(use_fixed_test_components=True) as runner,
        isolated_components_venv(runner),
    ):
        result = runner.invoke(
            "utils",
            "inspect-component",
            "dagster_test.components.SimplePipesScriptComponent",
            "--component-schema",
            "--defs-yaml-schema",
        )
        assert_runner_result(result, exit_0=False)
        assert (
            "Only one of --description, --scaffold-params-schema, --component-schema, and --defs-yaml-schema can be specified."
            in result.output
        )


def test_utils_inspect_component_type_undefined_component_type_fails() -> None:
    with (
        ProxyRunner.test(use_fixed_test_components=True) as runner,
        isolated_components_venv(runner),
    ):
        result = runner.invoke(
            "utils",
            "inspect-component",
            "fake.Fake",
        )
        assert_runner_result(result, exit_0=False)
        assert "No registry object `fake.Fake` is registered" in result.output


def test_generate_defs_yaml_schema_function():
    """Test the _generate_defs_yaml_schema function directly with an example component schema."""

    # Create a simple entry_snap with a trivial component schema
    class MockEntrySnap:
        def __init__(self, component_schema=None):
            self.component_schema = component_schema

    # Test with a simple component schema
    simple_schema = {
        "type": "object",
        "properties": {
            "name": {"type": "string", "title": "Name"},
            "enabled": {"type": "boolean", "default": True, "title": "Enabled"},
        },
        "required": ["name"],
        "additionalProperties": False,
        "title": "ExampleComponentModel",
    }

    entry_snap = MockEntrySnap(component_schema=simple_schema)
    component_type = "example.ExampleComponent"

    # Call the function directly
    result_schema = _generate_defs_yaml_schema(component_type, entry_snap)

    # Verify the structure matches ComponentFileModel
    assert "properties" in result_schema
    assert "type" in result_schema["properties"]
    assert "attributes" in result_schema["properties"]
    assert "template_vars_module" in result_schema["properties"]
    assert "requirements" in result_schema["properties"]
    assert "post_processing" in result_schema["properties"]

    # Verify the type field is constrained to the specific component
    assert result_schema["properties"]["type"]["const"] == component_type
    assert result_schema["properties"]["type"]["default"] == component_type

    # Verify the attributes field contains our simple schema
    assert result_schema["properties"]["attributes"] == simple_schema

    # Verify other fields are properly typed
    assert "ComponentRequirementsModel" in result_schema.get("$defs", {})

    # Test with no component schema
    entry_snap_empty = MockEntrySnap(component_schema=None)
    result_schema_empty = _generate_defs_yaml_schema("example.EmptyComponent", entry_snap_empty)

    # Should still have all the ComponentFileModel fields but attributes should be generic
    assert "properties" in result_schema_empty
    assert result_schema_empty["properties"]["type"]["const"] == "example.EmptyComponent"
    # When no component schema, attributes should have the original field definition from ComponentFileModel
    assert "attributes" in result_schema_empty["properties"]


def test_generate_defs_yaml_schema_json_output():
    """Test that _generate_defs_yaml_schema produces valid JSON schema string output."""
    from dagster_dg_cli.cli.utils import _serialize_json_schema

    # Create a simple entry_snap with a trivial component schema
    class MockEntrySnap:
        def __init__(self, component_schema=None):
            self.component_schema = component_schema

    # Test with a simple component schema
    simple_schema = {
        "type": "object",
        "properties": {
            "database_name": {
                "type": "string",
                "title": "Database Name",
                "description": "The name of the database",
            }
        },
        "required": ["database_name"],
        "additionalProperties": False,
        "title": "TrivialComponentModel",
    }

    entry_snap = MockEntrySnap(component_schema=simple_schema)
    component_type = "example.TrivialComponent"

    # Generate the schema and serialize to JSON string
    result_schema = _generate_defs_yaml_schema(component_type, entry_snap)
    json_string = _serialize_json_schema(result_schema)

    # Verify it's valid JSON
    parsed_back = json.loads(json_string)
    assert parsed_back == result_schema

    # Verify the JSON string contains expected elements
    assert '"const": "example.TrivialComponent"' in json_string
    assert '"database_name"' in json_string
    assert '"ComponentRequirementsModel"' in json_string
    assert '"template_vars_module"' in json_string

    # Verify the JSON is properly formatted (indented)
    assert json_string.count("\n") > 10  # Should be multi-line formatted
    assert "    " in json_string  # Should have indentation


def test_generate_defs_yaml_schema_complete_output():
    """Test _generate_defs_yaml_schema with expected complete JSON schema dictionary output."""
    from dagster_dg_cli.cli.utils import _serialize_json_schema

    # Create a simple entry_snap with a trivial component schema
    class MockEntrySnap:
        def __init__(self, component_schema=None):
            self.component_schema = component_schema

    # Simple component schema for testing
    trivial_schema = {
        "type": "object",
        "properties": {"config_path": {"type": "string", "title": "Config Path"}},
        "required": ["config_path"],
        "additionalProperties": False,
        "title": "TrivialExampleModel",
    }

    entry_snap = MockEntrySnap(component_schema=trivial_schema)
    component_type = "example.TrivialExample"

    # Generate the schema and serialize to JSON string
    result_schema = _generate_defs_yaml_schema(component_type, entry_snap)
    json_output = _serialize_json_schema(result_schema)

    # Parse the JSON string back to dictionary for easier assertion
    parsed_output = json.loads(json_output)

    # Assert against the expected dictionary structure
    expected_dict = {
        "$defs": {
            "ComponentRequirementsModel": {
                "description": "Describes dependencies for a component to load.",
                "properties": {
                    "env": {
                        "anyOf": [{"items": {"type": "string"}, "type": "array"}, {"type": "null"}],
                        "default": None,
                        "title": "Env",
                    }
                },
                "title": "ComponentRequirementsModel",
                "type": "object",
            }
        },
        "additionalProperties": False,
        "properties": {
            "type": {
                "const": "example.TrivialExample",
                "default": "example.TrivialExample",
                "title": "Type",
                "type": "string",
            },
            "attributes": {
                "type": "object",
                "properties": {"config_path": {"type": "string", "title": "Config Path"}},
                "required": ["config_path"],
                "additionalProperties": False,
                "title": "TrivialExampleModel",
            },
            "template_vars_module": {
                "anyOf": [{"type": "string"}, {"type": "null"}],
                "default": None,
                "title": "Template Vars Module",
            },
            "requirements": {
                "anyOf": [{"$ref": "#/$defs/ComponentRequirementsModel"}, {"type": "null"}],
                "default": None,
            },
            "post_processing": {
                "anyOf": [{"additionalProperties": True, "type": "object"}, {"type": "null"}],
                "default": None,
                "title": "Post Processing",
            },
        },
        "title": "exampleTrivialExampleComponentFileModel",
        "type": "object",
    }

    assert parsed_output == expected_dict
