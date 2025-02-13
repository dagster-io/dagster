import json
import subprocess
import textwrap
from pathlib import Path

import pytest
from dagster_dg.utils import (
    cross_platfrom_string_path,
    ensure_dagster_dg_tests_import,
    set_toml_value,
)

ensure_dagster_dg_tests_import()

from dagster_dg_tests.utils import (
    ProxyRunner,
    assert_runner_result,
    isolated_example_code_location_foo_bar,
    isolated_example_deployment_foo,
    modify_pyproject_toml,
    standardize_box_characters,
)

# ########################
# ##### SCAFFOLD
# ########################


def test_component_scaffold_dynamic_subcommand_generation() -> None:
    with ProxyRunner.test() as runner, isolated_example_code_location_foo_bar(runner):
        result = runner.invoke("component", "scaffold", "--help")
        assert_runner_result(result)

        normalized_output = standardize_box_characters(result.output)
        # These are wrapped in a table so it's hard to check exact output.
        for line in [
            "╭─ Commands",
            "│ all_metadata_empty_asset@dagster_components.test",
            "│ complex_schema_asset@dagster_components.test",
            "│ simple_asset@dagster_components.test",
            "│ simple_pipes_script_asset@dagster_components.test",
        ]:
            assert standardize_box_characters(line) in normalized_output


@pytest.mark.parametrize("in_deployment", [True, False])
def test_component_scaffold_no_params_success(in_deployment: bool) -> None:
    with (
        ProxyRunner.test() as runner,
        isolated_example_code_location_foo_bar(runner, in_deployment),
    ):
        result = runner.invoke(
            "component",
            "scaffold",
            "all_metadata_empty_asset@dagster_components.test",
            "qux",
        )
        assert_runner_result(result)
        assert Path("foo_bar/components/qux").exists()
        component_yaml_path = Path("foo_bar/components/qux/component.yaml")
        assert component_yaml_path.exists()
        assert (
            "type: all_metadata_empty_asset@dagster_components.test"
            in component_yaml_path.read_text()
        )


@pytest.mark.parametrize("in_deployment", [True, False])
def test_component_scaffold_json_params_success(in_deployment: bool) -> None:
    with (
        ProxyRunner.test() as runner,
        isolated_example_code_location_foo_bar(runner, in_deployment),
    ):
        result = runner.invoke(
            "component",
            "scaffold",
            "simple_pipes_script_asset@dagster_components.test",
            "qux",
            "--json-params",
            '{"asset_key": "foo", "filename": "hello.py"}',
        )
        assert_runner_result(result)
        assert Path("foo_bar/components/qux").exists()
        assert Path("foo_bar/components/qux/hello.py").exists()
        component_yaml_path = Path("foo_bar/components/qux/component.yaml")
        assert component_yaml_path.exists()
        assert (
            "type: simple_pipes_script_asset@dagster_components.test"
            in component_yaml_path.read_text()
        )


@pytest.mark.parametrize("in_deployment", [True, False])
def test_component_scaffold_key_value_params_success(in_deployment: bool) -> None:
    with (
        ProxyRunner.test() as runner,
        isolated_example_code_location_foo_bar(runner, in_deployment),
    ):
        result = runner.invoke(
            "component",
            "scaffold",
            "simple_pipes_script_asset@dagster_components.test",
            "qux",
            "--asset-key=foo",
            "--filename=hello.py",
        )
        assert_runner_result(result)
        assert Path("foo_bar/components/qux").exists()
        assert Path("foo_bar/components/qux/hello.py").exists()
        component_yaml_path = Path("foo_bar/components/qux/component.yaml")
        assert component_yaml_path.exists()
        assert (
            "type: simple_pipes_script_asset@dagster_components.test"
            in component_yaml_path.read_text()
        )


def test_component_scaffold_json_params_and_key_value_params_fails() -> None:
    with ProxyRunner.test() as runner, isolated_example_code_location_foo_bar(runner):
        result = runner.invoke(
            "component",
            "scaffold",
            "simple_pipes_script_asset@dagster_components.test",
            "qux",
            "--json-params",
            '{"filename": "hello.py"}',
            "--filename=hello.py",
        )
        assert_runner_result(result, exit_0=False)
        assert (
            "Detected params passed as both --json-params and individual options" in result.output
        )


def test_component_scaffold_undefined_component_type_fails() -> None:
    with ProxyRunner.test() as runner, isolated_example_code_location_foo_bar(runner):
        result = runner.invoke("component", "scaffold", "fake@fake", "qux")
        assert_runner_result(result, exit_0=False)
        assert "No component type `fake@fake` is registered" in result.output


def test_component_scaffold_outside_code_location_fails() -> None:
    with ProxyRunner.test() as runner, isolated_example_deployment_foo(runner):
        result = runner.invoke("component", "scaffold", "bar@baz", "qux")
        assert_runner_result(result, exit_0=False)
        assert "must be run inside a Dagster code location directory" in result.output


def test_scaffold_component_command_with_non_matching_package_name():
    with ProxyRunner.test() as runner, isolated_example_code_location_foo_bar(runner):
        #  move the module from foo_bar to module_not_same_as_code_location
        python_module = Path("foo_bar")
        python_module.rename("module_not_same_as_code_location")

        result = runner.invoke(
            "component", "scaffold", "all_metadata_empty_asset@dagster_components.test", "qux"
        )
        assert_runner_result(result, exit_0=False)
        assert (
            "Could not find expected package `foo_bar` in the current environment. Components expects the package name to match the directory name of the code location."
            in str(result.exception)
        )


def test_component_scaffold_with_no_dagster_components_fails() -> None:
    with ProxyRunner.test() as runner, isolated_example_code_location_foo_bar(runner):
        result = runner.invoke(
            "component",
            "scaffold",
            "simple_pipes_script_asset@dagster_components.test",
            "qux",
            env={"PATH": "/dev/null"},
        )
        assert_runner_result(result, exit_0=False)
        assert "Could not find the `dagster-components` executable" in result.output


@pytest.mark.parametrize("in_deployment", [True, False])
def test_component_scaffold_already_exists_fails(in_deployment: bool) -> None:
    with (
        ProxyRunner.test() as runner,
        isolated_example_code_location_foo_bar(runner, in_deployment),
    ):
        result = runner.invoke(
            "component",
            "scaffold",
            "all_metadata_empty_asset@dagster_components.test",
            "qux",
        )
        assert_runner_result(result)
        result = runner.invoke(
            "component",
            "scaffold",
            "all_metadata_empty_asset@dagster_components.test",
            "qux",
        )
        assert_runner_result(result, exit_0=False)
        assert "already exists" in result.output


def test_component_scaffold_succeeds_non_default_component_package() -> None:
    with ProxyRunner.test() as runner, isolated_example_code_location_foo_bar(runner):
        alt_lib_path = Path("foo_bar/_components")
        alt_lib_path.mkdir(parents=True)
        with modify_pyproject_toml() as toml:
            set_toml_value(toml, ("tool", "dg", "component_package"), "foo_bar._components")
        result = runner.invoke(
            "component",
            "scaffold",
            "all_metadata_empty_asset@dagster_components.test",
            "qux",
        )
        assert_runner_result(result)
        assert Path("foo_bar/_components/qux").exists()
        component_yaml_path = Path("foo_bar/_components/qux/component.yaml")
        assert component_yaml_path.exists()
        assert (
            "type: all_metadata_empty_asset@dagster_components.test"
            in component_yaml_path.read_text()
        )


def test_component_scaffold_fails_components_package_does_not_exist() -> None:
    with ProxyRunner.test() as runner, isolated_example_code_location_foo_bar(runner):
        with modify_pyproject_toml() as toml:
            set_toml_value(toml, ("tool", "dg", "component_package"), "bar._components")
        result = runner.invoke(
            "component",
            "scaffold",
            "all_metadata_empty_asset@dagster_components.test",
            "qux",
        )
        assert_runner_result(result, exit_0=False)
        assert "Components package `bar._components` is not installed" in str(result.exception)


def test_component_scaffold_succeeds_scaffolded_component_type() -> None:
    with ProxyRunner.test() as runner, isolated_example_code_location_foo_bar(runner):
        result = runner.invoke("component-type", "scaffold", "baz")
        assert_runner_result(result)
        assert Path("foo_bar/lib/baz.py").exists()

        result = runner.invoke("component", "scaffold", "baz@foo_bar", "qux")
        assert_runner_result(result)
        assert Path("foo_bar/components/qux").exists()
        component_yaml_path = Path("foo_bar/components/qux/component.yaml")
        assert component_yaml_path.exists()
        assert "type: baz@foo_bar" in component_yaml_path.read_text()


# ##### REAL COMPONENTS


dbt_project_path = Path("../stub_code_locations/dbt_project_location/components/jaffle_shop")


@pytest.mark.parametrize(
    "params",
    [
        ["--json-params", json.dumps({"project_path": str(dbt_project_path)})],
        ["--project-path", str(dbt_project_path)],
    ],
)
def test_scaffold_dbt_project_instance(params) -> None:
    with (
        ProxyRunner.test(use_test_component_lib=False) as runner,
        isolated_example_code_location_foo_bar(runner),
    ):
        # We need to add dagster-dbt also because we are using editable installs. Only
        # direct dependencies will be resolved by uv.tool.sources.
        subprocess.run(["uv", "add", "dagster-components[dbt]", "dagster-dbt"], check=True)
        result = runner.invoke(
            "component",
            "scaffold",
            "dbt_project@dagster_components",
            "my_project",
            *params,
        )
        assert_runner_result(result)
        assert Path("foo_bar/components/my_project").exists()

        component_yaml_path = Path("foo_bar/components/my_project/component.yaml")
        assert component_yaml_path.exists()
        assert "type: dbt_project@dagster_components" in component_yaml_path.read_text()
        assert (
            cross_platfrom_string_path(
                "stub_code_locations/dbt_project_location/components/jaffle_shop"
            )
            in component_yaml_path.read_text()
        )


# ########################
# ##### LIST
# ########################


def test_list_components_succeeds():
    with ProxyRunner.test() as runner, isolated_example_code_location_foo_bar(runner):
        result = runner.invoke(
            "component",
            "scaffold",
            "all_metadata_empty_asset@dagster_components.test",
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


def test_list_components_with_no_dagster_components_fails() -> None:
    with ProxyRunner.test() as runner, isolated_example_code_location_foo_bar(runner):
        result = runner.invoke("component", "list", env={"PATH": "/dev/null"})
        assert_runner_result(result, exit_0=False)
        assert "Could not find the `dagster-components` executable" in result.output
