import json
from pathlib import Path

from click.testing import CliRunner
from dagster_components.cli import cli
from dagster_components.utils import ensure_dagster_components_tests_import

ensure_dagster_components_tests_import()

from dagster_components_tests.utils import temp_code_location_bar


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
                "qux",
                "--json-params",
                '{"asset_key": "my_asset", "filename": "my_asset.py"}',
            ],
        )
        assert result.exit_code == 0
        assert Path("bar/components/qux/my_asset.py").exists()
