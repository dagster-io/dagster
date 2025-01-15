import json
import subprocess
import textwrap
from pathlib import Path

import pytest
from dagster_dg.utils import ensure_dagster_dg_tests_import

ensure_dagster_dg_tests_import()

from dagster_dg_tests.utils import (
    ProxyRunner,
    assert_runner_result,
    isolated_example_code_location_bar,
    isolated_example_deployment_foo,
    modify_pyproject_toml,
)

# ########################
# ##### SCAFFOLD
# ########################


def test_component_scaffold_dynamic_subcommand_generation() -> None:
    with ProxyRunner.test() as runner, isolated_example_code_location_bar(runner):
        result = runner.invoke("component", "scaffold", "--help")
        assert_runner_result(result)
        assert (
            textwrap.dedent("""
            Commands:
              dagster_components.test.all_metadata_empty_asset
              dagster_components.test.complex_schema_asset
              dagster_components.test.simple_asset
              dagster_components.test.simple_pipes_script_asset
        """).strip()
            in result.output
        )


@pytest.mark.parametrize("in_deployment", [True, False])
def test_component_scaffold_no_params_success(in_deployment: bool) -> None:
    with ProxyRunner.test() as runner, isolated_example_code_location_bar(runner, in_deployment):
        result = runner.invoke(
            "component",
            "scaffold",
            "dagster_components.test.all_metadata_empty_asset",
            "qux",
        )
        assert_runner_result(result)
        assert Path("bar/components/qux").exists()
        component_yaml_path = Path("bar/components/qux/component.yaml")
        assert component_yaml_path.exists()
        assert (
            "type: dagster_components.test.all_metadata_empty_asset"
            in component_yaml_path.read_text()
        )


@pytest.mark.parametrize("in_deployment", [True, False])
def test_component_scaffold_json_params_success(in_deployment: bool) -> None:
    with ProxyRunner.test() as runner, isolated_example_code_location_bar(runner, in_deployment):
        result = runner.invoke(
            "component",
            "scaffold",
            "dagster_components.test.simple_pipes_script_asset",
            "qux",
            "--json-params",
            '{"asset_key": "foo", "filename": "hello.py"}',
        )
        assert_runner_result(result)
        assert Path("bar/components/qux").exists()
        assert Path("bar/components/qux/hello.py").exists()
        component_yaml_path = Path("bar/components/qux/component.yaml")
        assert component_yaml_path.exists()
        assert (
            "type: dagster_components.test.simple_pipes_script_asset"
            in component_yaml_path.read_text()
        )


@pytest.mark.parametrize("in_deployment", [True, False])
def test_component_scaffold_key_value_params_success(in_deployment: bool) -> None:
    with ProxyRunner.test() as runner, isolated_example_code_location_bar(runner, in_deployment):
        result = runner.invoke(
            "component",
            "scaffold",
            "dagster_components.test.simple_pipes_script_asset",
            "qux",
            "--asset-key=foo",
            "--filename=hello.py",
        )
        assert_runner_result(result)
        assert Path("bar/components/qux").exists()
        assert Path("bar/components/qux/hello.py").exists()
        component_yaml_path = Path("bar/components/qux/component.yaml")
        assert component_yaml_path.exists()
        assert (
            "type: dagster_components.test.simple_pipes_script_asset"
            in component_yaml_path.read_text()
        )


def test_component_scaffold_json_params_and_key_value_params_fails() -> None:
    with ProxyRunner.test() as runner, isolated_example_code_location_bar(runner):
        result = runner.invoke(
            "component",
            "scaffold",
            "dagster_components.test.simple_pipes_script_asset",
            "qux",
            "--json-params",
            '{"filename": "hello.py"}',
            "--filename=hello.py",
        )
        assert_runner_result(result, exit_0=False)
        assert (
            "Detected params passed as both --json-params and individual options" in result.output
        )


def test_component_scaffold_outside_code_location_fails() -> None:
    with ProxyRunner.test() as runner, isolated_example_deployment_foo(runner):
        result = runner.invoke("component", "scaffold", "bar.baz", "qux")
        assert_runner_result(result, exit_0=False)
        assert "must be run inside a Dagster code location directory" in result.output


@pytest.mark.parametrize("in_deployment", [True, False])
def test_component_scaffold_already_exists_fails(in_deployment: bool) -> None:
    with ProxyRunner.test() as runner, isolated_example_code_location_bar(runner, in_deployment):
        result = runner.invoke(
            "component",
            "scaffold",
            "dagster_components.test.all_metadata_empty_asset",
            "qux",
        )
        assert_runner_result(result)
        result = runner.invoke(
            "component",
            "scaffold",
            "dagster_components.test.all_metadata_empty_asset",
            "qux",
        )
        assert_runner_result(result, exit_0=False)
        assert "already exists" in result.output


def test_component_scaffold_succeeds_non_default_component_package() -> None:
    with ProxyRunner.test() as runner, isolated_example_code_location_bar(runner):
        alt_lib_path = Path("bar/_components")
        alt_lib_path.mkdir(parents=True)
        with modify_pyproject_toml() as pyproject_toml:
            pyproject_toml["tool"]["dg"]["component_package"] = "bar._components"
        result = runner.invoke(
            "component",
            "scaffold",
            "dagster_components.test.all_metadata_empty_asset",
            "qux",
        )
        assert_runner_result(result)
        assert Path("bar/_components/qux").exists()
        component_yaml_path = Path("bar/_components/qux/component.yaml")
        assert component_yaml_path.exists()
        assert (
            "type: dagster_components.test.all_metadata_empty_asset"
            in component_yaml_path.read_text()
        )


def test_component_scaffold_fails_components_package_does_not_exist() -> None:
    with ProxyRunner.test() as runner, isolated_example_code_location_bar(runner):
        with modify_pyproject_toml() as pyproject_toml:
            pyproject_toml["tool"]["dg"]["component_package"] = "bar._components"
        result = runner.invoke(
            "component",
            "scaffold",
            "dagster_components.test.all_metadata_empty_asset",
            "qux",
        )
        assert_runner_result(result, exit_0=False)
        assert "Components package `bar._components` is not installed" in str(result.exception)


def test_component_scaffold_succeeds_scaffolded_component_type() -> None:
    with ProxyRunner.test() as runner, isolated_example_code_location_bar(runner):
        result = runner.invoke("component-type", "scaffold", "baz")
        assert_runner_result(result)
        assert Path("bar/lib/baz.py").exists()

        result = runner.invoke("component", "scaffold", "bar.baz", "qux")
        assert_runner_result(result)
        assert Path("bar/components/qux").exists()
        component_yaml_path = Path("bar/components/qux/component.yaml")
        assert component_yaml_path.exists()
        assert "type: bar.baz" in component_yaml_path.read_text()


# ##### REAL COMPONENTS


dbt_project_path = "../stub_code_locations/dbt_project_location/components/jaffle_shop"


@pytest.mark.parametrize(
    "params",
    [
        ["--json-params", json.dumps({"project_path": str(dbt_project_path)})],
        ["--project-path", dbt_project_path],
    ],
)
def test_scaffold_dbt_project_instance(params) -> None:
    with (
        ProxyRunner.test(use_test_component_lib=False) as runner,
        isolated_example_code_location_bar(runner),
    ):
        # We need to add dagster-dbt also because we are using editable installs. Only
        # direct dependencies will be resolved by uv.tool.sources.
        subprocess.run(["uv", "add", "dagster-components[dbt]", "dagster-dbt"], check=True)
        result = runner.invoke(
            "component",
            "scaffold",
            "dagster_components.dbt_project",
            "my_project",
            *params,
        )
        assert_runner_result(result)
        assert Path("bar/components/my_project").exists()

        component_yaml_path = Path("bar/components/my_project/component.yaml")
        assert component_yaml_path.exists()
        assert "type: dagster_components.dbt_project" in component_yaml_path.read_text()
        assert (
            "stub_code_locations/dbt_project_location/components/jaffle_shop"
            in component_yaml_path.read_text()
        )


# ########################
# ##### LIST
# ########################


def test_list_components_succeeds():
    with ProxyRunner.test() as runner, isolated_example_code_location_bar(runner):
        result = runner.invoke(
            "component",
            "scaffold",
            "dagster_components.test.all_metadata_empty_asset",
            "qux",
        )
        assert_runner_result(result)
        result = runner.invoke("component", "list")
        assert_runner_result(result)
        assert (
            result.output.strip()
            == textwrap.dedent("""
            qux
        """).strip()
        )


def test_list_components_command_outside_code_location_fails() -> None:
    with ProxyRunner.test() as runner, runner.isolated_filesystem():
        result = runner.invoke("component", "list")
        assert_runner_result(result, exit_0=False)
        assert "must be run inside a Dagster code location directory" in result.output
