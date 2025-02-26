import json
from pathlib import Path

import pytest
from click.testing import CliRunner
from dagster._core.test_utils import new_cwd
from dagster_components.cli import cli
from dagster_components.utils import ensure_dagster_components_tests_import
from jsonschema import Draft202012Validator, ValidationError

ensure_dagster_components_tests_import()

from dagster_components_tests.utils import create_project_from_components, temp_code_location_bar


# Test that the global --use-test-component-lib flag changes the registered components
def test_global_test_flag():
    runner: CliRunner = CliRunner()

    # standard
    result = runner.invoke(cli, ["list", "component-types"])
    assert result.exit_code == 0
    default_result_keys = list(json.loads(result.output).keys())
    assert len(default_result_keys) > 0

    result = runner.invoke(
        cli, ["--builtin-component-lib", "dagster_components.test", "list", "component-types"]
    )
    assert result.exit_code == 0
    test_result_keys = list(json.loads(result.output).keys())
    assert len(default_result_keys) > 0

    assert default_result_keys != test_result_keys


def test_list_component_types_command():
    runner = CliRunner()

    result = runner.invoke(
        cli, ["--builtin-component-lib", "dagster_components.test", "list", "component-types"]
    )
    assert result.exit_code == 0
    result = json.loads(result.output)

    assert list(result.keys()) == [
        "dagster_components.lib.test.AllMetadataEmptyAsset",
        "dagster_components.lib.test.ComplexSchemaAsset",
        "dagster_components.lib.test.SimpleAsset",
        "dagster_components.lib.test.SimplePipesScriptAsset",
    ]

    assert result["dagster_components.lib.test.SimpleAsset"] == {
        "name": "SimpleAsset",
        "namespace": "dagster_components.lib.test",
        "summary": "A simple asset that returns a constant string value.",
        "description": "A simple asset that returns a constant string value.",
        "scaffold_params_schema": None,
        "component_schema": {
            "properties": {
                "asset_key": {"title": "Asset Key", "type": "string"},
                "value": {"title": "Value", "type": "string"},
            },
            "required": ["asset_key", "value"],
            "title": "SimpleAssetSchema",
            "type": "object",
        },
    }

    pipes_script_params_schema = {
        "properties": {
            "asset_key": {"title": "Asset Key", "type": "string"},
            "filename": {"title": "Filename", "type": "string"},
        },
        "required": ["asset_key", "filename"],
        "title": "SimplePipesScriptAssetSchema",
        "type": "object",
    }

    assert result["dagster_components.lib.test.SimplePipesScriptAsset"] == {
        "name": "SimplePipesScriptAsset",
        "namespace": "dagster_components.lib.test",
        "summary": "A simple asset that runs a Python script with the Pipes subprocess client.",
        "description": "A simple asset that runs a Python script with the Pipes subprocess client.\n\nBecause it is a pipes asset, no value is returned.",
        "scaffold_params_schema": pipes_script_params_schema,
        "component_schema": pipes_script_params_schema,
    }


def test_list_module_components_types() -> None:
    """Tests that the list CLI picks up on local components."""
    runner = CliRunner()

    with create_project_from_components(
        "definitions/local_component_sample",
        "definitions/other_local_component_sample",
        "definitions/default_file",
    ) as tmpdir:
        with new_cwd(str(tmpdir)):
            result = runner.invoke(
                cli,
                [
                    "--builtin-component-lib",
                    "dagster_components.test",
                    "list",
                    "component-types",
                    "--no-entry-points",
                    "my_location.components.local_component_sample",
                ],
            )

            assert result.exit_code == 0, str(result.stdout)

            result = json.loads(result.output)
            assert len(result) == 1
            assert set(result.keys()) == {
                "my_location.components.local_component_sample.MyComponent"
            }

            # Add a second module
            result = runner.invoke(
                cli,
                [
                    "--builtin-component-lib",
                    "dagster_components.test",
                    "list",
                    "component-types",
                    "--no-entry-points",
                    "my_location.components.local_component_sample",
                    "my_location.components.other_local_component_sample",
                ],
            )

            assert result.exit_code == 0, str(result.stdout)

            result = json.loads(result.output)
            assert len(result) == 2
            assert set(result.keys()) == {
                "my_location.components.local_component_sample.MyComponent",
                "my_location.components.other_local_component_sample.MyNewComponent",
            }

            # Add another, non-local component directory, which no-ops
            result = runner.invoke(
                cli,
                [
                    "--builtin-component-lib",
                    "dagster_components.test",
                    "list",
                    "component-types",
                    "--no-entry-points",
                    "my_location.components.local_component_sample",
                    "my_location.components.other_local_component_sample",
                    "my_location.components.default_file",
                ],
            )

            assert result.exit_code == 0, str(result.stdout)

            result = json.loads(result.output)
            assert len(result) == 2


def test_all_components_schema_command():
    runner = CliRunner()

    result = runner.invoke(
        cli, ["--builtin-component-lib", "dagster_components.test", "list", "all-components-schema"]
    )
    assert result.exit_code == 0
    result = json.loads(result.output)

    component_type_keys = [
        "ComplexSchemaAsset",
        "SimpleAsset",
        "SimplePipesScriptAsset",
    ]

    assert result["anyOf"] == [
        {"$ref": f"#/$defs/{component_type_key}"} for component_type_key in component_type_keys
    ]

    # Sanity check each of the component type schemas has a constant type property matching the
    # fully scoped component type key
    for component_type_key in component_type_keys:
        component_type_schema_def = result["$defs"][component_type_key]
        assert "type" in component_type_schema_def["properties"]
        assert (
            component_type_schema_def["properties"]["type"]["default"]
            == f"dagster_components.lib.test.{component_type_key}"
        )
        assert (
            component_type_schema_def["properties"]["type"]["const"]
            == f"dagster_components.lib.test.{component_type_key}"
        )
        assert "attributes" in component_type_schema_def["properties"]

    top_level_component_validator = Draft202012Validator(schema=result)
    top_level_component_validator.validate(
        {
            "type": "dagster_components.lib.test.SimpleAsset",
            "attributes": {"asset_key": "my_asset", "value": "my_value"},
        }
    )
    with pytest.raises(ValidationError):
        top_level_component_validator.validate(
            {
                "type": "dagster_components.lib.test.SimpleAsset",
                "attributes": {"asset_key": "my_asset", "value": "my_value"},
                "extra_key": "extra_value",
            }
        )


def test_scaffold_component_command():
    runner = CliRunner()

    with temp_code_location_bar():
        result = runner.invoke(
            cli,
            [
                "--builtin-component-lib",
                "dagster_components.test",
                "scaffold",
                "component",
                "dagster_components.lib.test.SimplePipesScriptAsset",
                "bar/components/qux",
                "--json-params",
                '{"asset_key": "my_asset", "filename": "my_asset.py"}',
            ],
        )
        assert result.exit_code == 0
        assert Path("bar/components/qux/my_asset.py").exists()
