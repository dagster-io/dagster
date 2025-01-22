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
    default_result_keys = list(item["key"] for item in json.loads(result.output))
    assert len(default_result_keys) > 0

    result = runner.invoke(
        cli, ["--builtin-component-lib", "dagster_components.test", "list", "component-types"]
    )
    assert result.exit_code == 0
    test_result_keys = list(item["key"] for item in json.loads(result.output))
    assert len(default_result_keys) > 0

    assert default_result_keys != test_result_keys


def test_list_component_types_command():
    runner = CliRunner()

    result = runner.invoke(
        cli,
        ["--builtin-component-lib", "dagster_components.test", "list", "component-types"],
        catch_exceptions=False,
    )
    assert result.exit_code == 0
    result = json.loads(result.output)
    result_as_dict = {item["key"]: item["value"] for item in result}

    assert list(result_as_dict.keys()) == [
        "dagster_components.test.all_metadata_empty_asset",
        "dagster_components.test.complex_schema_asset",
        "dagster_components.test.simple_asset",
        "dagster_components.test.simple_pipes_script_asset",
    ]

    assert result_as_dict["dagster_components.test.simple_asset"] == {
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
        "component_directory": None,
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

    assert result_as_dict["dagster_components.test.simple_pipes_script_asset"] == {
        "name": "simple_pipes_script_asset",
        "package": "dagster_components.test",
        "summary": "A simple asset that runs a Python script with the Pipes subprocess client.",
        "description": "A simple asset that runs a Python script with the Pipes subprocess client.\n\nBecause it is a pipes asset, no value is returned.",
        "scaffold_params_schema": pipes_script_params_schema,
        "component_params_schema": pipes_script_params_schema,
        "component_directory": None,
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
            assert result[0]["directory"] == "my_location/components/local_component_sample"
            assert result[0]["key"] == ".my_component"

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
