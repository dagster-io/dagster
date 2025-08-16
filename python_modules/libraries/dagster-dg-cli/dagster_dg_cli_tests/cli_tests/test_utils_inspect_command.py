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

    # Verify the core structure is present
    assert "properties" in parsed_output
    assert "type" in parsed_output["properties"]
    assert "attributes" in parsed_output["properties"]
    assert "post_processing" in parsed_output["properties"]

    # Verify type is constrained to the specific component
    assert parsed_output["properties"]["type"]["const"] == component_type
    assert parsed_output["properties"]["type"]["default"] == component_type

    # Verify attributes contains the component-specific schema
    assert parsed_output["properties"]["attributes"] == trivial_schema

    # Verify post_processing has the ComponentPostProcessingModel structure
    post_processing = parsed_output["properties"]["post_processing"]
    assert "anyOf" in post_processing
    assert len(post_processing["anyOf"]) == 2
    assert post_processing["anyOf"][1] == {"type": "null"}  # nullable

    # Verify the ComponentPostProcessingModel schema structure
    post_processing_obj = post_processing["anyOf"][0]
    assert post_processing_obj["type"] == "object"
    assert "assets" in post_processing_obj["properties"]

    # Verify the assets field contains AssetPostProcessorModel items
    assets_field = post_processing_obj["properties"]["assets"]
    assert (
        "anyOf" in assets_field
    )  # Assets field is now a Union[tuple[AssetPostProcessor], None, str]

    # Find the array option in the anyOf
    array_option = None
    for option in assets_field["anyOf"]:
        if option.get("type") == "array":
            array_option = option
            break

    assert array_option is not None, "Should have an array option in assets anyOf"
    assert "items" in array_option
    assert "$ref" in array_option["items"]  # Items should be a reference to AssetPostProcessorModel

    # Verify AssetPostProcessorModel is in $defs and has the correct structure
    assert "$defs" in parsed_output
    asset_post_processor_ref = array_option["items"]["$ref"]
    model_name = asset_post_processor_ref.split("/")[
        -1
    ]  # Extract model name from #/$defs/ModelName
    assert model_name in parsed_output["$defs"]

    asset_post_processor = parsed_output["$defs"][model_name]
    assert "target" in asset_post_processor["properties"]
    assert "operation" in asset_post_processor["properties"]
    assert "attributes" in asset_post_processor["properties"]

    # Verify that attributes references AssetsDefUpdateKwargsModel
    attributes_field = asset_post_processor["properties"]["attributes"]
    assert "anyOf" in attributes_field  # attributes is also a union

    # Find the AssetsDefUpdateKwargsModel reference
    kwargs_ref = None
    for option in attributes_field["anyOf"]:
        if "$ref" in option and "AssetsDefUpdateKwargsModel" in option["$ref"]:
            kwargs_ref = option["$ref"]
            break

    assert kwargs_ref is not None, "Should reference AssetsDefUpdateKwargsModel"
    kwargs_model_name = kwargs_ref.split("/")[-1]
    assert kwargs_model_name in parsed_output["$defs"]

    # Verify AssetsDefUpdateKwargs has all the expected fields including unions
    kwargs_schema = parsed_output["$defs"][kwargs_model_name]
    assert "deps" in kwargs_schema["properties"]
    assert "metadata" in kwargs_schema["properties"]
    assert "tags" in kwargs_schema["properties"]
    assert "owners" in kwargs_schema["properties"]
    assert "partitions_def" in kwargs_schema["properties"]

    # Verify partitions_def has the correct union structure
    partitions_def = kwargs_schema["properties"]["partitions_def"]
    assert "anyOf" in partitions_def
    # Should have references to all partition definition models plus string option
    partition_refs = [opt for opt in partitions_def["anyOf"] if "$ref" in opt]
    assert len(partition_refs) >= 5  # At least 5 partition definition types

    # Verify $defs contains partition definition models
    assert "$defs" in parsed_output
    assert "HourlyPartitionsDefinitionModel" in parsed_output["$defs"]
    assert "DailyPartitionsDefinitionModel" in parsed_output["$defs"]
