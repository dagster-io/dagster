import textwrap

from dagster_dg.utils import ensure_dagster_dg_tests_import

ensure_dagster_dg_tests_import()

from dagster_dg_tests.utils import (
    ProxyRunner,
    assert_runner_result,
    isolated_example_code_location_bar,
)


def test_info_component_type_all_metadata_success():
    runner = ProxyRunner.test()
    with isolated_example_code_location_bar(runner):
        result = runner.invoke(
            "info",
            "component-type",
            "dagster_components.test.simple_pipes_script_asset",
        )
        assert_runner_result(result)
        assert (
            result.output.strip()
            == textwrap.dedent("""
            dagster_components.test.simple_pipes_script_asset

            Description:

            A simple asset that runs a Python script with the Pipes subprocess client.

            Because it is a pipes asset, no value is returned.

            Generate params schema:

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
                "title": "SimplePipesScriptAssetParams",
                "type": "object"
            }

            Component params schema:

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
                "title": "SimplePipesScriptAssetParams",
                "type": "object"
            }
        """).strip()
        )


def test_info_component_type_all_metadata_empty_success():
    runner = ProxyRunner.test()
    with isolated_example_code_location_bar(runner):
        result = runner.invoke(
            "info",
            "component-type",
            "dagster_components.test.all_metadata_empty_asset",
        )
        assert_runner_result(result)
        assert (
            result.output.strip()
            == textwrap.dedent("""
            dagster_components.test.all_metadata_empty_asset
        """).strip()
        )


def test_info_component_type_flag_fields_success():
    runner = ProxyRunner.test()
    with isolated_example_code_location_bar(runner):
        result = runner.invoke(
            "info",
            "component-type",
            "dagster_components.test.simple_pipes_script_asset",
            "--description",
        )
        assert_runner_result(result)
        assert (
            result.output.strip()
            == textwrap.dedent("""
            A simple asset that runs a Python script with the Pipes subprocess client.

            Because it is a pipes asset, no value is returned.
        """).strip()
        )

        result = runner.invoke(
            "info",
            "component-type",
            "dagster_components.test.simple_pipes_script_asset",
            "--generate-params-schema",
        )
        assert_runner_result(result)
        assert (
            result.output.strip()
            == textwrap.dedent("""
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
                "title": "SimplePipesScriptAssetParams",
                "type": "object"
            }
        """).strip()
        )

        result = runner.invoke(
            "info",
            "component-type",
            "dagster_components.test.simple_pipes_script_asset",
            "--component-params-schema",
        )
        assert_runner_result(result)
        assert (
            result.output.strip()
            == textwrap.dedent("""
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
                "title": "SimplePipesScriptAssetParams",
                "type": "object"
            }
        """).strip()
        )


def test_info_component_type_outside_code_location_fails() -> None:
    runner = ProxyRunner.test()
    with runner.isolated_filesystem():
        result = runner.invoke(
            "info",
            "component-type",
            "dagster_components.test.simple_pipes_script_asset",
            "--component-params-schema",
        )
        assert_runner_result(result, exit_0=False)
        assert "must be run inside a Dagster code location directory" in result.output


def test_info_component_type_multiple_flags_fails() -> None:
    runner = ProxyRunner.test()
    with isolated_example_code_location_bar(runner):
        result = runner.invoke(
            "info",
            "component-type",
            "dagster_components.test.simple_pipes_script_asset",
            "--description",
            "--generate-params-schema",
        )
        assert_runner_result(result, exit_0=False)
        assert (
            "Only one of --description, --generate-params-schema, and --component-params-schema can be specified."
            in result.output
        )
