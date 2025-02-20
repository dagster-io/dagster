import textwrap

from dagster_dg.utils import ensure_dagster_dg_tests_import

ensure_dagster_dg_tests_import()

from dagster_dg_tests.utils import ProxyRunner, assert_runner_result, isolated_components_venv

# ########################
# ##### COMPONENT TYPE
# ########################

_EXPECTED_info_component_type_FULL = textwrap.dedent("""
    simple_pipes_script_asset@dagster_components.test

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
        "title": "SimplePipesScriptAssetSchema",
        "type": "object"
    }

    Component schema:

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
        "title": "SimplePipesScriptAssetSchema",
        "type": "object"
    }
""").strip()


def test_info_component_type_all_metadata_success():
    with ProxyRunner.test() as runner, isolated_components_venv(runner):
        result = runner.invoke(
            "info",
            "component-type",
            "simple_pipes_script_asset@dagster_components.test",
        )
        assert_runner_result(result)
        assert result.output.strip().endswith(_EXPECTED_info_component_type_FULL)


def test_info_component_type_all_metadata_empty_success():
    with ProxyRunner.test() as runner, isolated_components_venv(runner):
        result = runner.invoke(
            "info",
            "component-type",
            "all_metadata_empty_asset@dagster_components.test",
        )
        assert_runner_result(result)
        assert result.output.strip().endswith(
            textwrap.dedent("""
                all_metadata_empty_asset@dagster_components.test
            """).strip()
        )


def test_info_component_type_flag_fields_success():
    with ProxyRunner.test() as runner, isolated_components_venv(runner):
        result = runner.invoke(
            "info",
            "component-type",
            "simple_pipes_script_asset@dagster_components.test",
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
            "info",
            "component-type",
            "simple_pipes_script_asset@dagster_components.test",
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
                    "title": "SimplePipesScriptAssetSchema",
                    "type": "object"
                }
            """).strip()
        )

        result = runner.invoke(
            "info",
            "component-type",
            "simple_pipes_script_asset@dagster_components.test",
            "--component-schema",
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
                    "title": "SimplePipesScriptAssetSchema",
                    "type": "object"
                }
            """).strip()
        )


def test_info_component_type_multiple_flags_fails() -> None:
    with ProxyRunner.test() as runner, isolated_components_venv(runner):
        result = runner.invoke(
            "info",
            "component-type",
            "simple_pipes_script_asset@dagster_components.test",
            "--description",
            "--scaffold-params-schema",
        )
        assert_runner_result(result, exit_0=False)
        assert (
            "Only one of --description, --scaffold-params-schema, and --component-schema can be specified."
            in result.output
        )


def test_info_component_type_undefined_component_type_fails() -> None:
    with ProxyRunner.test() as runner, isolated_components_venv(runner):
        result = runner.invoke(
            "info",
            "component-type",
            "fake@fake",
        )
        assert_runner_result(result, exit_0=False)
        assert "No component type `fake@fake` is registered" in result.output
