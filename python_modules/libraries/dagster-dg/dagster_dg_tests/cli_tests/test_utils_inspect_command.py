import textwrap

from dagster_dg.utils import ensure_dagster_dg_tests_import

ensure_dagster_dg_tests_import()

from dagster_dg_tests.utils import ProxyRunner, assert_runner_result, isolated_components_venv

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
            "inspect-component-type",
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
            "inspect-component-type",
            "dagster_test.components.AllMetadataEmptyComponent",
        )
        assert_runner_result(result)
        assert result.output.strip().endswith(
            textwrap.dedent("""
                dagster_test.components.AllMetadataEmptyComponent
            """).strip()
        )


def test_utils_inspect_component_type_flag_fields_success():
    with (
        ProxyRunner.test(use_fixed_test_components=True) as runner,
        isolated_components_venv(runner),
    ):
        result = runner.invoke(
            "utils",
            "inspect-component-type",
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
            "inspect-component-type",
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
            "inspect-component-type",
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


def test_utils_inspect_component_type_multiple_flags_fails() -> None:
    with (
        ProxyRunner.test(use_fixed_test_components=True) as runner,
        isolated_components_venv(runner),
    ):
        result = runner.invoke(
            "utils",
            "inspect-component-type",
            "dagster_test.components.SimplePipesScriptComponent",
            "--description",
            "--scaffold-params-schema",
        )
        assert_runner_result(result, exit_0=False)
        assert (
            "Only one of --description, --scaffold-params-schema, and --component-schema can be specified."
            in result.output
        )


def test_utils_inspect_component_type_undefined_component_type_fails() -> None:
    with (
        ProxyRunner.test(use_fixed_test_components=True) as runner,
        isolated_components_venv(runner),
    ):
        result = runner.invoke(
            "utils",
            "inspect-component-type",
            "fake.Fake",
        )
        assert_runner_result(result, exit_0=False)
        assert "No component type `fake.Fake` is registered" in result.output
