import json
import textwrap

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
            "--defs-yaml-json-schema",
        )
        assert_runner_result(result)
        # Check key parts of the complete defs.yaml schema
        output_json = json.loads(result.output.strip())

        # Verify top-level structure
        assert output_json["type"] == "object"
        assert not output_json["additionalProperties"]
        assert "type" in output_json["required"]
        assert "attributes" in output_json["required"]

        # Verify all expected top-level properties exist
        expected_properties = {
            "type",
            "attributes",
            "template_vars_module",
            "requirements",
            "post_processing",
        }
        assert set(output_json["properties"].keys()) == expected_properties

        # Verify the attributes section contains the component schema
        attributes_schema = output_json["properties"]["attributes"]
        assert not attributes_schema["additionalProperties"]
        assert attributes_schema["properties"]["asset_key"]["type"] == "string"
        assert attributes_schema["properties"]["filename"]["type"] == "string"
        assert set(attributes_schema["required"]) == {"asset_key", "filename"}

        # Verify the requirements section has the expected structure
        requirements_schema = output_json["properties"]["requirements"]
        assert "$ref" in requirements_schema["anyOf"][0]
        assert "#/$defs/ComponentRequirementsModel" in requirements_schema["anyOf"][0]["$ref"]

        # Test --defs-yaml-schema flag
        result = runner.invoke(
            "utils",
            "inspect-component",
            "dagster_test.components.SimplePipesScriptComponent",
            "--defs-yaml-schema",
        )
        assert_runner_result(result)
        # Check that the output contains the expected schema template structure
        output_yaml = result.output.strip()
        assert "# Template with instructions" in output_yaml
        assert "type: dagster_test.components.SimplePipesScriptComponent  # Required" in output_yaml
        assert "attributes:  # Optional: Attributes details" in output_yaml
        assert "asset_key: <string>  # Required:" in output_yaml
        assert "filename: <string>  # Required:" in output_yaml
        # Should NOT contain example values
        assert "# EXAMPLE VALUES:" not in output_yaml
        assert '"example_string"' not in output_yaml

        # Test --defs-yaml-example-values flag
        result = runner.invoke(
            "utils",
            "inspect-component",
            "dagster_test.components.SimplePipesScriptComponent",
            "--defs-yaml-example-values",
        )
        assert_runner_result(result)
        # Check that the output contains the expected example values
        output_yaml = result.output.strip()
        assert 'type: "dagster_test.components.SimplePipesScriptComponent"' in output_yaml
        assert 'asset_key: "example_string"' in output_yaml
        assert 'filename: "example_string"' in output_yaml
        # Should NOT contain schema template instructions
        assert "# Template with instructions" not in output_yaml
        assert "# Required" not in output_yaml


def test_utils_inspect_component_type_defs_yaml_schema_full_output():
    with (
        ProxyRunner.test(use_fixed_test_components=True) as runner,
        isolated_components_venv(runner),
    ):
        result = runner.invoke(
            "utils",
            "inspect-component",
            "dagster_test.components.SimplePipesScriptComponent",
            "--defs-yaml-schema",
        )
        assert_runner_result(result)
        assert (
            result.output.strip()
            == textwrap.dedent("""
            # Template with instructions
            type: dagster_test.components.SimplePipesScriptComponent  # Required
            attributes:  # Optional: Attributes details
              asset_key: <string>  # Required: 
              filename: <string>  # Required: 
        """).strip()
        )


def test_utils_inspect_component_type_defs_yaml_example_values_full_output():
    with (
        ProxyRunner.test(use_fixed_test_components=True) as runner,
        isolated_components_venv(runner),
    ):
        result = runner.invoke(
            "utils",
            "inspect-component",
            "dagster_test.components.SimplePipesScriptComponent",
            "--defs-yaml-example-values",
        )
        assert_runner_result(result)
        assert (
            result.output.strip()
            == textwrap.dedent("""
            type: "dagster_test.components.SimplePipesScriptComponent"
            attributes:
              asset_key: "example_string"
              filename: "example_string"
        """).strip()
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
            "Only one of --description, --scaffold-params-schema, --component-schema, --defs-yaml-json-schema, --defs-yaml-schema, --defs-yaml-example-values, and --template can be specified."
            in result.output
        )


def test_utils_inspect_component_type_template_flag_success() -> None:
    with (
        ProxyRunner.test(use_fixed_test_components=True) as runner,
        isolated_components_venv(runner),
    ):
        result = runner.invoke(
            "utils",
            "inspect-component",
            "dagster_test.components.SimplePipesScriptComponent",
            "--template",
        )
        assert_runner_result(result)

        # Should contain template headers and structure
        assert "# Template for SimplePipesScriptComponent" in result.output
        assert "# Example Values:" in result.output
        assert "asset_key:" in result.output or "filename:" in result.output

        # Should show type annotations with comments
        assert "string #" in result.output


def test_utils_inspect_component_type_defs_yaml_flags_with_other_flags_fails() -> None:
    with (
        ProxyRunner.test(use_fixed_test_components=True) as runner,
        isolated_components_venv(runner),
    ):
        # Test --defs-yaml-schema with another flag
        result = runner.invoke(
            "utils",
            "inspect-component",
            "dagster_test.components.SimplePipesScriptComponent",
            "--defs-yaml-json-schema",
            "--defs-yaml-schema",
        )
        assert_runner_result(result, exit_0=False)
        assert (
            "Only one of --description, --scaffold-params-schema, --component-schema, --defs-yaml-json-schema, --defs-yaml-schema, --defs-yaml-example-values, and --template can be specified."
            in result.output
        )

        # Test --defs-yaml-example-values with another flag
        result = runner.invoke(
            "utils",
            "inspect-component",
            "dagster_test.components.SimplePipesScriptComponent",
            "--description",
            "--defs-yaml-example-values",
        )
        assert_runner_result(result, exit_0=False)
        assert (
            "Only one of --description, --scaffold-params-schema, --component-schema, --defs-yaml-json-schema, --defs-yaml-schema, --defs-yaml-example-values, and --template can be specified."
            in result.output
        )

        # Test both new flags together
        result = runner.invoke(
            "utils",
            "inspect-component",
            "dagster_test.components.SimplePipesScriptComponent",
            "--defs-yaml-schema",
            "--defs-yaml-example-values",
        )
        assert_runner_result(result, exit_0=False)
        assert (
            "Only one of --description, --scaffold-params-schema, --component-schema, --defs-yaml-json-schema, --defs-yaml-schema, --defs-yaml-example-values, and --template can be specified."
            in result.output
        )


def test_utils_inspect_component_type_template_multiple_flags_fails() -> None:
    """Test that template flag conflicts with other flags."""
    with (
        ProxyRunner.test(use_fixed_test_components=True) as runner,
        isolated_components_venv(runner),
    ):
        result = runner.invoke(
            "utils",
            "inspect-component",
            "dagster_test.components.SimplePipesScriptComponent",
            "--template",
            "--component-schema",
        )
        assert_runner_result(result, exit_0=False)
        assert (
            "Only one of --description, --scaffold-params-schema, --component-schema, --defs-yaml-json-schema, --defs-yaml-schema, --defs-yaml-example-values, and --template can be specified."
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
