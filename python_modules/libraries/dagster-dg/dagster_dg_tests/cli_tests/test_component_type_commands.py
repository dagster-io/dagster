import textwrap
from pathlib import Path

from dagster_dg.component import RemoteComponentRegistry
from dagster_dg.context import DgContext
from dagster_dg.utils import ensure_dagster_dg_tests_import

ensure_dagster_dg_tests_import()

from dagster_dg_tests.utils import (
    ProxyRunner,
    assert_runner_result,
    isolated_components_venv,
    isolated_example_component_library_foo_bar,
    isolated_example_deployment_foo,
    modify_pyproject_toml,
)

# ########################
# ##### SCAFFOLD
# ########################


def test_component_type_scaffold_success() -> None:
    with (
        ProxyRunner.test() as runner,
        isolated_example_component_library_foo_bar(runner),
    ):
        result = runner.invoke("component-type", "scaffold", "baz")
        assert_runner_result(result)
        assert Path("foo_bar/lib/baz.py").exists()
        dg_context = DgContext.from_config_file_discovery_and_cli_config(Path.cwd(), {})
        registry = RemoteComponentRegistry.from_dg_context(dg_context)
        assert registry.has_global("foo_bar.baz")


def test_component_type_scaffold_outside_component_library_fails() -> None:
    with ProxyRunner.test() as runner, isolated_example_deployment_foo(runner):
        result = runner.invoke("component-type", "scaffold", "baz")
        assert_runner_result(result, exit_0=False)
        assert "must be run inside a Dagster component library directory" in result.output


def test_component_type_scaffold_with_no_dagster_components_fails() -> None:
    with (
        ProxyRunner.test() as runner,
        isolated_example_component_library_foo_bar(runner),
    ):
        result = runner.invoke("component-type", "scaffold", "baz", env={"PATH": "/dev/null"})
        assert_runner_result(result, exit_0=False)
        assert "Could not find the `dagster-components` executable" in result.output


def test_component_type_scaffold_already_exists_fails() -> None:
    with (
        ProxyRunner.test() as runner,
        isolated_example_component_library_foo_bar(runner),
    ):
        result = runner.invoke("component-type", "scaffold", "baz")
        assert_runner_result(result)
        result = runner.invoke("component-type", "scaffold", "baz")
        assert_runner_result(result, exit_0=False)
        assert "already exists" in result.output


def test_component_type_scaffold_succeeds_non_default_component_lib_package() -> None:
    with (
        ProxyRunner.test() as runner,
        isolated_example_component_library_foo_bar(runner, lib_package_name="foo_bar._lib"),
    ):
        result = runner.invoke(
            "component-type",
            "scaffold",
            "baz",
        )
        assert_runner_result(result)
        assert Path("foo_bar/_lib/baz.py").exists()
        dg_context = DgContext.from_config_file_discovery_and_cli_config(Path.cwd(), {})
        registry = RemoteComponentRegistry.from_dg_context(dg_context)
        assert registry.has_global("foo_bar.baz")


def test_component_type_scaffold_fails_components_lib_package_does_not_exist() -> None:
    with (
        ProxyRunner.test() as runner,
        isolated_example_component_library_foo_bar(runner),
    ):
        with modify_pyproject_toml() as pyproject_toml:
            pyproject_toml["tool"]["dg"]["component_lib_package"] = "foo_bar._lib"
        result = runner.invoke(
            "component-type",
            "scaffold",
            "baz",
        )
        assert_runner_result(result, exit_0=False)
        assert "Components lib package `foo_bar._lib` is not installed" in str(result.exception)


# ########################
# ##### DOCS
# ########################


def test_component_type_docs_success():
    with ProxyRunner.test() as runner, isolated_components_venv(runner):
        result = runner.invoke(
            "component-type",
            "docs",
            "dagster_components.test.complex_schema_asset",
        )
        assert_runner_result(result)


def test_component_type_docs_with_no_dagster_components_fails() -> None:
    with (
        ProxyRunner.test() as runner,
        isolated_components_venv(runner),
    ):
        result = runner.invoke(
            "component-type",
            "docs",
            "dagster_components.test.complex_schema_asset",
            env={"PATH": "/dev/null"},
        )
        assert_runner_result(result, exit_0=False)
        assert "Could not find the `dagster-components` executable" in result.output


# ########################
# ##### INFO
# ########################

_EXPECTED_COMPONENT_TYPE_INFO_FULL = textwrap.dedent("""
    dagster_components.test.simple_pipes_script_asset

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


def test_component_type_info_all_metadata_success():
    with ProxyRunner.test() as runner, isolated_components_venv(runner):
        result = runner.invoke(
            "component-type",
            "info",
            "dagster_components.test.simple_pipes_script_asset",
        )
        assert_runner_result(result)
        assert result.output.strip() == _EXPECTED_COMPONENT_TYPE_INFO_FULL


def test_component_type_info_all_metadata_empty_success():
    with ProxyRunner.test() as runner, isolated_components_venv(runner):
        result = runner.invoke(
            "component-type",
            "info",
            "dagster_components.test.all_metadata_empty_asset",
        )
        assert_runner_result(result)
        assert (
            result.output.strip()
            == textwrap.dedent("""
                dagster_components.test.all_metadata_empty_asset
            """).strip()
        )


def test_component_type_info_flag_fields_success():
    with ProxyRunner.test() as runner, isolated_components_venv(runner):
        result = runner.invoke(
            "component-type",
            "info",
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
            "component-type",
            "info",
            "dagster_components.test.simple_pipes_script_asset",
            "--scaffold-params-schema",
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
            "component-type",
            "info",
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


def test_component_type_info_multiple_flags_fails() -> None:
    with ProxyRunner.test() as runner, isolated_components_venv(runner):
        result = runner.invoke(
            "component-type",
            "info",
            "dagster_components.test.simple_pipes_script_asset",
            "--description",
            "--scaffold-params-schema",
        )
        assert_runner_result(result, exit_0=False)
        assert (
            "Only one of --description, --scaffold-params-schema, and --component-params-schema can be specified."
            in result.output
        )


def test_component_type_info_with_no_dagster_components_fails() -> None:
    with (
        ProxyRunner.test() as runner,
        isolated_components_venv(runner),
    ):
        result = runner.invoke(
            "component-type",
            "info",
            "dagster_components.test.simple_pipes_script_asset",
            env={"PATH": "/dev/null"},
        )
        assert_runner_result(result, exit_0=False)
        assert "Could not find the `dagster-components` executable" in result.output


# ########################
# ##### LIST
# ########################

_EXPECTED_COMPONENT_TYPES = textwrap.dedent("""
    ┏━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━┳━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━┓
    ┃ Component Type                                    ┃ Summary                                                          ┃
    ┡━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━╇━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━┩
    │ dagster_components.test.all_metadata_empty_asset  │                                                                  │
    │ dagster_components.test.complex_schema_asset      │ An asset that has a complex params schema.                       │
    │ dagster_components.test.simple_asset              │ A simple asset that returns a constant string value.             │
    │ dagster_components.test.simple_pipes_script_asset │ A simple asset that runs a Python script with the Pipes          │
    │                                                   │ subprocess client.                                               │
    └───────────────────────────────────────────────────┴──────────────────────────────────────────────────────────────────┘
""").strip()


def test_list_component_types_success():
    with ProxyRunner.test() as runner, isolated_components_venv(runner):
        result = runner.invoke("component-type", "list")
        assert_runner_result(result)
        assert result.output.strip() == _EXPECTED_COMPONENT_TYPES


def test_component_type_list_with_no_dagster_components_fails() -> None:
    with (
        ProxyRunner.test() as runner,
        isolated_components_venv(runner),
    ):
        result = runner.invoke("component-type", "list", env={"PATH": "/dev/null"})
        assert_runner_result(result, exit_0=False)
        assert "Could not find the `dagster-components` executable" in result.output
