import json
import os
import subprocess
from pathlib import Path

import pytest
import tomlkit
from dagster_dg.component import RemoteComponentRegistry
from dagster_dg.component_key import GlobalComponentKey
from dagster_dg.context import DgContext
from dagster_dg.utils import (
    cross_platfrom_string_path,
    discover_git_root,
    ensure_dagster_dg_tests_import,
    get_toml_value,
    pushd,
    set_toml_value,
)

ensure_dagster_dg_tests_import()

from dagster_dg_tests.utils import (
    ProxyRunner,
    assert_runner_result,
    clear_module_from_cache,
    isolated_example_code_location_foo_bar,
    isolated_example_component_library_foo_bar,
    isolated_example_deployment_foo,
    modify_pyproject_toml,
    standardize_box_characters,
)

# ########################
# ##### CODE LOCATION
# ########################

# At this time all of our tests are against an editable install of dagster-components. The reason
# for this is that this package should always be tested against the corresponding version of
# dagster-components (i.e. from the same commit), and the only way to achieve this right now is
# using the editable install variant of `dg scaffold code-location`.
#
# Ideally we would have a way to still use the matching dagster-components without using the
# editable install variant, but this will require somehow configuring uv to ensure that it builds
# and returns the local version of the package.


def test_scaffold_code_location_inside_deployment_success(monkeypatch) -> None:
    # Remove when we are able to test without editable install
    dagster_git_repo_dir = discover_git_root(Path(__file__))
    monkeypatch.setenv("DAGSTER_GIT_REPO_DIR", str(dagster_git_repo_dir))

    with ProxyRunner.test() as runner, isolated_example_deployment_foo(runner):
        result = runner.invoke("scaffold", "code-location", "foo-bar", "--use-editable-dagster")
        assert_runner_result(result)
        assert Path("code_locations/foo-bar").exists()
        assert Path("code_locations/foo-bar/foo_bar").exists()
        assert Path("code_locations/foo-bar/foo_bar/lib").exists()
        assert Path("code_locations/foo-bar/foo_bar/components").exists()
        assert Path("code_locations/foo-bar/foo_bar_tests").exists()
        assert Path("code_locations/foo-bar/pyproject.toml").exists()

        # Check TOML content
        toml = tomlkit.parse(Path("code_locations/foo-bar/pyproject.toml").read_text())
        assert (
            get_toml_value(toml, ("tool", "dagster", "module_name"), str) == "foo_bar.definitions"
        )
        assert get_toml_value(toml, ("tool", "dagster", "code_location_name"), str) == "foo-bar"

        # Check venv created
        assert Path("code_locations/foo-bar/.venv").exists()
        assert Path("code_locations/foo-bar/uv.lock").exists()

        # Restore when we are able to test without editable install
        # with open("code_locations/bar/pyproject.toml") as f:
        #     toml = tomlkit.parse(f.read())
        #
        #     # No tool.uv.sources added without --use-editable-dagster
        #     assert "uv" not in toml["tool"]

        # Check cache was populated
        with pushd("code_locations/foo-bar"):
            result = runner.invoke("list", "component-type", "--verbose")
            assert_runner_result(result)
            assert "CACHE [hit]" in result.output


def test_scaffold_code_location_outside_deployment_success(monkeypatch) -> None:
    # Remove when we are able to test without editable install
    dagster_git_repo_dir = discover_git_root(Path(__file__))
    monkeypatch.setenv("DAGSTER_GIT_REPO_DIR", str(dagster_git_repo_dir))

    with ProxyRunner.test() as runner, runner.isolated_filesystem(), clear_module_from_cache("bar"):
        result = runner.invoke("scaffold", "code-location", "foo-bar", "--use-editable-dagster")
        assert_runner_result(result)
        assert Path("foo-bar").exists()
        assert Path("foo-bar/foo_bar").exists()
        assert Path("foo-bar/foo_bar/lib").exists()
        assert Path("foo-bar/foo_bar/components").exists()
        assert Path("foo-bar/foo_bar_tests").exists()
        assert Path("foo-bar/pyproject.toml").exists()

        # Check venv created
        assert Path("foo-bar/.venv").exists()
        assert Path("foo-bar/uv.lock").exists()


@pytest.mark.parametrize("mode", ["env_var", "arg"])
def test_scaffold_code_location_editable_dagster_success(mode: str, monkeypatch) -> None:
    dagster_git_repo_dir = discover_git_root(Path(__file__))
    if mode == "env_var":
        monkeypatch.setenv("DAGSTER_GIT_REPO_DIR", str(dagster_git_repo_dir))
        editable_args = ["--use-editable-dagster", "--"]
    else:
        editable_args = ["--use-editable-dagster", str(dagster_git_repo_dir)]
    with ProxyRunner.test() as runner, isolated_example_deployment_foo(runner):
        result = runner.invoke("scaffold", "code-location", *editable_args, "foo-bar")
        assert_runner_result(result)
        assert Path("code_locations/foo-bar").exists()
        assert Path("code_locations/foo-bar/pyproject.toml").exists()
        with open("code_locations/foo-bar/pyproject.toml") as f:
            toml = tomlkit.parse(f.read())
            assert get_toml_value(toml, ("tool", "uv", "sources", "dagster"), dict) == {
                "path": str(dagster_git_repo_dir / "python_modules" / "dagster"),
                "editable": True,
            }
            assert get_toml_value(toml, ("tool", "uv", "sources", "dagster-pipes"), dict) == {
                "path": str(dagster_git_repo_dir / "python_modules" / "dagster-pipes"),
                "editable": True,
            }
            assert get_toml_value(toml, ("tool", "uv", "sources", "dagster-webserver"), dict) == {
                "path": str(dagster_git_repo_dir / "python_modules" / "dagster-webserver"),
                "editable": True,
            }
            assert get_toml_value(toml, ("tool", "uv", "sources", "dagster-components"), dict) == {
                "path": str(
                    dagster_git_repo_dir / "python_modules" / "libraries" / "dagster-components"
                ),
                "editable": True,
            }
            # Check for presence of one random package with no component to ensure we are
            # preemptively adding all packages
            assert get_toml_value(toml, ("tool", "uv", "sources", "dagstermill"), dict) == {
                "path": str(dagster_git_repo_dir / "python_modules" / "libraries" / "dagstermill"),
                "editable": True,
            }


def test_scaffold_code_location_skip_venv_success() -> None:
    with ProxyRunner.test() as runner, runner.isolated_filesystem():
        result = runner.invoke("scaffold", "code-location", "--skip-venv", "foo-bar")
        assert_runner_result(result)
        assert Path("foo-bar").exists()
        assert Path("foo-bar/foo_bar").exists()
        assert Path("foo-bar/foo_bar/lib").exists()
        assert Path("foo-bar/foo_bar/components").exists()
        assert Path("foo-bar/foo_bar_tests").exists()
        assert Path("foo-bar/pyproject.toml").exists()

        # Check venv not created
        assert not Path("foo-bar/.venv").exists()
        assert not Path("foo-bar/uv.lock").exists()


def test_scaffold_code_location_no_populate_cache_success() -> None:
    with ProxyRunner.test() as runner, runner.isolated_filesystem():
        result = runner.invoke("scaffold", "code-location", "--no-populate-cache", "foo-bar")
        assert_runner_result(result)
        assert Path("foo-bar").exists()
        assert Path("foo-bar/foo_bar").exists()
        assert Path("foo-bar/foo_bar/lib").exists()
        assert Path("foo-bar/foo_bar/components").exists()
        assert Path("foo-bar/foo_bar_tests").exists()
        assert Path("foo-bar/pyproject.toml").exists()

        # Check venv created
        assert Path("foo-bar/.venv").exists()
        assert Path("foo-bar/uv.lock").exists()

        with pushd("foo-bar"):
            result = runner.invoke("list", "component-type", "--verbose")
            assert_runner_result(result)
            assert "CACHE [miss]" in result.output


def test_scaffold_code_location_no_use_dg_managed_environment_success() -> None:
    with ProxyRunner.test() as runner, runner.isolated_filesystem():
        result = runner.invoke(
            "scaffold", "code-location", "--no-use-dg-managed-environment", "foo-bar"
        )
        assert_runner_result(result)
        assert Path("foo-bar").exists()
        assert Path("foo-bar/foo_bar").exists()
        assert Path("foo-bar/foo_bar/lib").exists()
        assert Path("foo-bar/foo_bar/components").exists()
        assert Path("foo-bar/foo_bar_tests").exists()
        assert Path("foo-bar/pyproject.toml").exists()

        # Check venv not created
        assert not Path("foo-bar/.venv").exists()
        assert not Path("foo-bar/uv.lock").exists()


def test_scaffold_code_location_editable_dagster_no_env_var_no_value_fails(monkeypatch) -> None:
    monkeypatch.setenv("DAGSTER_GIT_REPO_DIR", "")
    with ProxyRunner.test() as runner, isolated_example_deployment_foo(runner):
        result = runner.invoke("scaffold", "code-location", "--use-editable-dagster", "--", "bar")
        assert_runner_result(result, exit_0=False)
        assert "requires the `DAGSTER_GIT_REPO_DIR`" in result.output


def test_scaffold_code_location_already_exists_fails() -> None:
    with ProxyRunner.test() as runner, isolated_example_deployment_foo(runner):
        result = runner.invoke("scaffold", "code-location", "bar", "--skip-venv")
        assert_runner_result(result)
        result = runner.invoke("scaffold", "code-location", "bar", "--skip-venv")
        assert_runner_result(result, exit_0=False)
        assert "already exists" in result.output


# ########################
# ##### COMPONENT
# ########################


def test_scaffold_component_dynamic_subcommand_generation() -> None:
    with ProxyRunner.test() as runner, isolated_example_code_location_foo_bar(runner):
        result = runner.invoke("scaffold", "component", "--help")
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
def test_scaffold_component_no_params_success(in_deployment: bool) -> None:
    with (
        ProxyRunner.test() as runner,
        isolated_example_code_location_foo_bar(runner, in_deployment),
    ):
        result = runner.invoke(
            "scaffold",
            "component",
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
def test_scaffold_component_json_params_success(in_deployment: bool) -> None:
    with (
        ProxyRunner.test() as runner,
        isolated_example_code_location_foo_bar(runner, in_deployment),
    ):
        result = runner.invoke(
            "scaffold",
            "component",
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
def test_scaffold_component_key_value_params_success(in_deployment: bool) -> None:
    with (
        ProxyRunner.test() as runner,
        isolated_example_code_location_foo_bar(runner, in_deployment),
    ):
        result = runner.invoke(
            "scaffold",
            "component",
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


def test_scaffold_component_json_params_and_key_value_params_fails() -> None:
    with ProxyRunner.test() as runner, isolated_example_code_location_foo_bar(runner):
        result = runner.invoke(
            "scaffold",
            "component",
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


def test_scaffold_component_undefined_component_type_fails() -> None:
    with ProxyRunner.test() as runner, isolated_example_code_location_foo_bar(runner):
        result = runner.invoke("scaffold", "component", "fake@fake", "qux")
        assert_runner_result(result, exit_0=False)
        assert "No component type `fake@fake` is registered" in result.output


def test_scaffold_component_command_with_non_matching_package_name():
    with ProxyRunner.test() as runner, isolated_example_code_location_foo_bar(runner):
        #  move the module from foo_bar to module_not_same_as_code_location
        python_module = Path("foo_bar")
        python_module.rename("module_not_same_as_code_location")

        result = runner.invoke(
            "scaffold", "component", "all_metadata_empty_asset@dagster_components.test", "qux"
        )
        assert_runner_result(result, exit_0=False)
        assert (
            "Could not find expected package `foo_bar` in the current environment. Components expects the package name to match the directory name of the code location."
            in str(result.exception)
        )


@pytest.mark.parametrize("in_deployment", [True, False])
def test_scaffold_component_already_exists_fails(in_deployment: bool) -> None:
    with (
        ProxyRunner.test() as runner,
        isolated_example_code_location_foo_bar(runner, in_deployment),
    ):
        result = runner.invoke(
            "scaffold",
            "component",
            "all_metadata_empty_asset@dagster_components.test",
            "qux",
        )
        assert_runner_result(result)
        result = runner.invoke(
            "scaffold",
            "component",
            "all_metadata_empty_asset@dagster_components.test",
            "qux",
        )
        assert_runner_result(result, exit_0=False)
        assert "already exists" in result.output


def test_scaffold_component_succeeds_non_default_component_package() -> None:
    with ProxyRunner.test() as runner, isolated_example_code_location_foo_bar(runner):
        alt_lib_path = Path("foo_bar/_components")
        alt_lib_path.mkdir(parents=True)
        with modify_pyproject_toml() as toml:
            set_toml_value(toml, ("tool", "dg", "component_package"), "foo_bar._components")
        result = runner.invoke(
            "scaffold",
            "component",
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


def test_scaffold_component_fails_components_package_does_not_exist() -> None:
    with ProxyRunner.test() as runner, isolated_example_code_location_foo_bar(runner):
        with modify_pyproject_toml() as toml:
            set_toml_value(toml, ("tool", "dg", "component_package"), "bar._components")
        result = runner.invoke(
            "scaffold",
            "component",
            "all_metadata_empty_asset@dagster_components.test",
            "qux",
        )
        assert_runner_result(result, exit_0=False)
        assert "Components package `bar._components` is not installed" in str(result.exception)


def test_scaffold_component_succeeds_scaffolded_component_type() -> None:
    with ProxyRunner.test() as runner, isolated_example_code_location_foo_bar(runner):
        result = runner.invoke("scaffold", "component-type", "baz")
        assert_runner_result(result)
        assert Path("foo_bar/lib/baz.py").exists()

        result = runner.invoke("scaffold", "component", "baz@foo_bar", "qux")
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
            "scaffold",
            "component",
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
# ##### COMPONENT TYPE
# ########################


def test_scaffold_component_type_success() -> None:
    with (
        ProxyRunner.test() as runner,
        isolated_example_component_library_foo_bar(runner),
    ):
        result = runner.invoke("scaffold", "component-type", "baz")
        assert_runner_result(result)
        assert Path("foo_bar/lib/baz.py").exists()
        dg_context = DgContext.from_config_file_discovery_and_cli_config(Path.cwd(), {})
        registry = RemoteComponentRegistry.from_dg_context(dg_context)
        assert registry.has_global(GlobalComponentKey(name="baz", namespace="foo_bar"))


def test_scaffold_component_type_already_exists_fails() -> None:
    with (
        ProxyRunner.test() as runner,
        isolated_example_component_library_foo_bar(runner),
    ):
        result = runner.invoke("scaffold", "component-type", "baz")
        assert_runner_result(result)
        result = runner.invoke("scaffold", "component-type", "baz")
        assert_runner_result(result, exit_0=False)
        assert "already exists" in result.output


def test_scaffold_component_type_succeeds_non_default_component_lib_package() -> None:
    with (
        ProxyRunner.test() as runner,
        isolated_example_component_library_foo_bar(runner, lib_package_name="foo_bar._lib"),
    ):
        result = runner.invoke(
            "scaffold",
            "component-type",
            "baz",
        )
        assert_runner_result(result)
        assert Path("foo_bar/_lib/baz.py").exists()
        dg_context = DgContext.from_config_file_discovery_and_cli_config(Path.cwd(), {})
        registry = RemoteComponentRegistry.from_dg_context(dg_context)
        assert registry.has_global(GlobalComponentKey(name="baz", namespace="foo_bar"))


def test_scaffold_component_type_fails_components_lib_package_does_not_exist() -> None:
    with (
        ProxyRunner.test() as runner,
        isolated_example_component_library_foo_bar(runner),
    ):
        with modify_pyproject_toml() as toml:
            set_toml_value(toml, ("tool", "dg", "component_lib_package"), "foo_bar._lib")
        result = runner.invoke(
            "scaffold",
            "component-type",
            "baz",
        )
        assert_runner_result(result, exit_0=False)
        assert "Components lib package `foo_bar._lib` is not installed" in str(result.exception)


# ########################
# ##### DEPLOYMENT
# ########################


def test_scaffold_deployment_command_success() -> None:
    with ProxyRunner.test() as runner, runner.isolated_filesystem():
        result = runner.invoke("scaffold", "deployment", "foo")
        assert_runner_result(result)
        assert Path("foo").exists()
        assert Path("foo/code_locations").exists()


def test_scaffold_deployment_command_already_exists_fails() -> None:
    with ProxyRunner.test() as runner, runner.isolated_filesystem():
        os.mkdir("foo")
        result = runner.invoke("scaffold", "deployment", "foo")
        assert_runner_result(result, exit_0=False)
        assert "already exists" in result.output
