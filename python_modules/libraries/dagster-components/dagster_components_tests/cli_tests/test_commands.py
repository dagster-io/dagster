import json
from pathlib import Path

from click.testing import CliRunner
from dagster._core.test_utils import new_cwd
from dagster_components.cli import cli
from dagster_components.utils import ensure_dagster_components_tests_import

ensure_dagster_components_tests_import()

from dagster_components_tests.utils import (
    create_code_location_from_components,
    temp_code_location_bar,
)


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
        "dagster_components.test.all_metadata_empty_asset",
        "dagster_components.test.complex_schema_asset",
        "dagster_components.test.simple_asset",
        "dagster_components.test.simple_pipes_script_asset",
    ]

    assert result["dagster_components.test.simple_asset"] == {
        "name": "simple_asset",
        "package": "dagster_components.test",
        "summary": "A simple asset that returns a constant string value.",
        "description": "A simple asset that returns a constant string value.",
        "scaffold_params_schema": None,
        "component_params_schema": {
            "properties": {
                "asset_key": {"title": "Asset Key", "type": "string"},
                "value": {"title": "Value", "type": "string"},
            },
            "required": ["asset_key", "value"],
            "title": "SimpleAssetParams",
            "type": "object",
        },
    }

    pipes_script_params_schema = {
        "properties": {
            "asset_key": {"title": "Asset Key", "type": "string"},
            "filename": {"title": "Filename", "type": "string"},
        },
        "required": ["asset_key", "filename"],
        "title": "SimplePipesScriptAssetParams",
        "type": "object",
    }

    assert result["dagster_components.test.simple_pipes_script_asset"] == {
        "name": "simple_pipes_script_asset",
        "package": "dagster_components.test",
        "summary": "A simple asset that runs a Python script with the Pipes subprocess client.",
        "description": "A simple asset that runs a Python script with the Pipes subprocess client.\n\nBecause it is a pipes asset, no value is returned.",
        "scaffold_params_schema": pipes_script_params_schema,
        "component_params_schema": pipes_script_params_schema,
    }


def test_list_local_components_types() -> None:
    """Tests that the list CLI picks up on local components."""
    runner = CliRunner()

    with create_code_location_from_components(
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
                    "local-component-types",
                    "my_location/components/local_component_sample",
                ],
            )

            assert result.exit_code == 0, str(result.stdout)

            result = json.loads(result.output)
            assert len(result) == 1
            assert set(result.keys()) == {"my_location/components/local_component_sample"}
            assert set(result["my_location/components/local_component_sample"].keys()) == {
                ".my_component"
            }

            # Add a second directory and local component
            result = runner.invoke(
                cli,
                [
                    "--builtin-component-lib",
                    "dagster_components.test",
                    "list",
                    "local-component-types",
                    "my_location/components/local_component_sample",
                    "my_location/components/other_local_component_sample",
                ],
            )

            assert result.exit_code == 0, str(result.stdout)

            result = json.loads(result.output)
            assert len(result) == 2

            # Add another, non-local component directory, which no-ops
            result = runner.invoke(
                cli,
                [
                    "--builtin-component-lib",
                    "dagster_components.test",
                    "list",
                    "local-component-types",
                    "my_location/components/local_component_sample",
                    "my_location/components/other_local_component_sample",
                    "my_location/components/default_file",
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
        "complex_schema_asset",
        "simple_asset",
        "simple_pipes_script_asset",
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
            == f"dagster_components.test.{component_type_key}"
        )
        assert (
            component_type_schema_def["properties"]["type"]["const"]
            == f"dagster_components.test.{component_type_key}"
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
                "dagster_components.test.simple_pipes_script_asset",
                "bar/components/qux",
                "--json-params",
                '{"asset_key": "my_asset", "filename": "my_asset.py"}',
            ],
        )
        assert result.exit_code == 0
        assert Path("bar/components/qux/my_asset.py").exists()
