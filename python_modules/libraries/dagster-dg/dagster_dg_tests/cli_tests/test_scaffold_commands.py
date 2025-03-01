import json
import shutil
import subprocess
from pathlib import Path

import pytest
import tomlkit
from dagster_dg.component import RemoteComponentRegistry
from dagster_dg.component_key import ComponentKey
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
    isolated_example_component_library_foo_bar,
    isolated_example_project_foo_bar,
    isolated_example_workspace,
    modify_pyproject_toml,
    standardize_box_characters,
)

# ########################
# ##### WORKSPACE
# ########################


def test_scaffold_workspace_command_success(monkeypatch) -> None:
    with ProxyRunner.test() as runner, runner.isolated_filesystem():
        result = runner.invoke("scaffold", "workspace")
        assert_runner_result(result)
        assert Path("dagster-workspace").exists()
        assert Path("dagster-workspace/pyproject.toml").exists()
        assert Path("dagster-workspace/projects").exists()
        assert Path("dagster-workspace/libraries").exists()

        result = runner.invoke("scaffold", "workspace")
        assert_runner_result(result, exit_0=False)
        assert "already exists" in result.output


def test_scaffold_workspace_command_name_override_success(monkeypatch) -> None:
    with ProxyRunner.test() as runner, runner.isolated_filesystem():
        result = runner.invoke("scaffold", "workspace", "my-workspace")
        assert_runner_result(result)
        assert Path("my-workspace").exists()
        assert Path("my-workspace/pyproject.toml").exists()
        assert Path("my-workspace/projects").exists()
        assert Path("my-workspace/libraries").exists()

        result = runner.invoke("scaffold", "workspace", "my-workspace")
        assert_runner_result(result, exit_0=False)
        assert "already exists" in result.output


# ########################
# ##### PROJECT
# ########################

# At this time all of our tests are against an editable install of dagster-components. The reason
# for this is that this package should always be tested against the corresponding version of
# dagster-components (i.e. from the same commit), and the only way to achieve this right now is
# using the editable install variant of `dg scaffold project`.
#
# Ideally we would have a way to still use the matching dagster-components without using the
# editable install variant, but this will require somehow configuring uv to ensure that it builds
# and returns the local version of the package.


def test_scaffold_project_inside_workspace_success(monkeypatch) -> None:
    # Remove when we are able to test without editable install
    dagster_git_repo_dir = discover_git_root(Path(__file__))
    monkeypatch.setenv("DAGSTER_GIT_REPO_DIR", str(dagster_git_repo_dir))

    with ProxyRunner.test() as runner, isolated_example_workspace(runner):
        result = runner.invoke(
            "scaffold", "project", "foo-bar", "--use-editable-dagster", "--verbose"
        )
        assert_runner_result(result)
        assert Path("projects/foo-bar").exists()
        assert Path("projects/foo-bar/foo_bar").exists()
        assert Path("projects/foo-bar/foo_bar/lib").exists()
        assert Path("projects/foo-bar/foo_bar/defs").exists()
        assert Path("projects/foo-bar/foo_bar_tests").exists()
        assert Path("projects/foo-bar/pyproject.toml").exists()

        # Check TOML content
        toml = tomlkit.parse(Path("projects/foo-bar/pyproject.toml").read_text())
        assert (
            get_toml_value(toml, ("tool", "dagster", "module_name"), str) == "foo_bar.definitions"
        )
        assert get_toml_value(toml, ("tool", "dagster", "code_location_name"), str) == "foo-bar"

        # Check venv created
        assert Path("projects/foo-bar/.venv").exists()
        assert Path("projects/foo-bar/uv.lock").exists()

        # Restore when we are able to test without editable install
        # with open("projects/bar/pyproject.toml") as f:
        #     toml = tomlkit.parse(f.read())
        #
        #     # No tool.uv.sources added without --use-editable-dagster
        #     assert "uv" not in toml["tool"]

        # Check cache was populated
        with pushd("projects/foo-bar"):
            result = runner.invoke("list", "component-type", "--verbose")
            assert_runner_result(result)
            assert "CACHE [hit]" in result.output


def test_scaffold_project_outside_workspace_success(monkeypatch) -> None:
    # Remove when we are able to test without editable install
    dagster_git_repo_dir = discover_git_root(Path(__file__))
    monkeypatch.setenv("DAGSTER_GIT_REPO_DIR", str(dagster_git_repo_dir))

    with ProxyRunner.test() as runner, runner.isolated_filesystem(), clear_module_from_cache("bar"):
        result = runner.invoke("scaffold", "project", "foo-bar", "--use-editable-dagster")
        assert_runner_result(result)
        assert Path("foo-bar").exists()
        assert Path("foo-bar/foo_bar").exists()
        assert Path("foo-bar/foo_bar/lib").exists()
        assert Path("foo-bar/foo_bar/defs").exists()
        assert Path("foo-bar/foo_bar_tests").exists()
        assert Path("foo-bar/pyproject.toml").exists()

        # Check venv created
        assert Path("foo-bar/.venv").exists()
        assert Path("foo-bar/uv.lock").exists()


@pytest.mark.parametrize("mode", ["env_var", "arg"])
def test_scaffold_project_editable_dagster_success(mode: str, monkeypatch) -> None:
    dagster_git_repo_dir = discover_git_root(Path(__file__))
    if mode == "env_var":
        monkeypatch.setenv("DAGSTER_GIT_REPO_DIR", str(dagster_git_repo_dir))
        editable_args = ["--use-editable-dagster", "--"]
    else:
        editable_args = ["--use-editable-dagster", str(dagster_git_repo_dir)]
    with ProxyRunner.test() as runner, isolated_example_workspace(runner):
        result = runner.invoke("scaffold", "project", *editable_args, "foo-bar")
        assert_runner_result(result)
        assert Path("projects/foo-bar").exists()
        assert Path("projects/foo-bar/pyproject.toml").exists()
        with open("projects/foo-bar/pyproject.toml") as f:
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


def test_scaffold_project_skip_venv_success() -> None:
    with ProxyRunner.test() as runner, runner.isolated_filesystem():
        result = runner.invoke("scaffold", "project", "--skip-venv", "foo-bar")
        assert_runner_result(result)
        assert Path("foo-bar").exists()
        assert Path("foo-bar/foo_bar").exists()
        assert Path("foo-bar/foo_bar/lib").exists()
        assert Path("foo-bar/foo_bar/defs").exists()
        assert Path("foo-bar/foo_bar_tests").exists()
        assert Path("foo-bar/pyproject.toml").exists()

        # Check venv not created
        assert not Path("foo-bar/.venv").exists()
        assert not Path("foo-bar/uv.lock").exists()


def test_scaffold_project_no_populate_cache_success(monkeypatch) -> None:
    dagster_git_repo_dir = discover_git_root(Path(__file__))
    monkeypatch.setenv("DAGSTER_GIT_REPO_DIR", str(dagster_git_repo_dir))
    with ProxyRunner.test() as runner, runner.isolated_filesystem():
        result = runner.invoke(
            "scaffold",
            "project",
            "--no-populate-cache",
            "foo-bar",
            "--use-editable-dagster",
        )
        assert_runner_result(result)
        assert Path("foo-bar").exists()
        assert Path("foo-bar/foo_bar").exists()
        assert Path("foo-bar/foo_bar/lib").exists()
        assert Path("foo-bar/foo_bar/defs").exists()
        assert Path("foo-bar/foo_bar_tests").exists()
        assert Path("foo-bar/pyproject.toml").exists()

        # Check venv created
        assert Path("foo-bar/.venv").exists()
        assert Path("foo-bar/uv.lock").exists()

        with pushd("foo-bar"):
            result = runner.invoke("list", "component-type", "--verbose")
            assert_runner_result(result)
            assert "CACHE [miss]" in result.output


def test_scaffold_project_no_use_dg_managed_environment_success(monkeypatch) -> None:
    dagster_git_repo_dir = discover_git_root(Path(__file__))
    monkeypatch.setenv("DAGSTER_GIT_REPO_DIR", str(dagster_git_repo_dir))
    with ProxyRunner.test() as runner, runner.isolated_filesystem():
        result = runner.invoke(
            "scaffold",
            "project",
            "--no-use-dg-managed-environment",
            "foo-bar",
            "--use-editable-dagster",
        )
        assert_runner_result(result)
        assert Path("foo-bar").exists()
        assert Path("foo-bar/foo_bar").exists()
        assert Path("foo-bar/foo_bar/lib").exists()
        assert Path("foo-bar/foo_bar/defs").exists()
        assert Path("foo-bar/foo_bar_tests").exists()
        assert Path("foo-bar/pyproject.toml").exists()

        # Check venv not created
        assert not Path("foo-bar/.venv").exists()
        assert not Path("foo-bar/uv.lock").exists()


def test_scaffold_project_editable_dagster_no_env_var_no_value_fails(monkeypatch) -> None:
    monkeypatch.setenv("DAGSTER_GIT_REPO_DIR", "")
    with ProxyRunner.test() as runner, isolated_example_workspace(runner):
        result = runner.invoke("scaffold", "project", "--use-editable-dagster", "--", "bar")
        assert_runner_result(result, exit_0=False)
        assert "requires the `DAGSTER_GIT_REPO_DIR`" in result.output


def test_scaffold_project_already_exists_fails() -> None:
    with ProxyRunner.test() as runner, isolated_example_workspace(runner):
        result = runner.invoke("scaffold", "project", "bar", "--skip-venv")
        assert_runner_result(result)
        result = runner.invoke("scaffold", "project", "bar", "--skip-venv")
        assert_runner_result(result, exit_0=False)
        assert "already exists" in result.output


# ########################
# ##### COMPONENT
# ########################


def test_scaffold_component_dynamic_subcommand_generation() -> None:
    with ProxyRunner.test() as runner, isolated_example_project_foo_bar(runner):
        result = runner.invoke("scaffold", "component", "--help")
        assert_runner_result(result)

        normalized_output = standardize_box_characters(result.output)
        # These are wrapped in a table so it's hard to check exact output.
        for line in [
            "╭─ Commands",
            "│ dagster_test.components.AllMetadataEmptyComponent",
            "│ dagster_test.components.ComplexAssetComponent",
            "│ dagster_test.components.SimpleAssetComponent",
            "│ dagster_test.components.SimplePipesScriptComponent",
        ]:
            assert standardize_box_characters(line) in normalized_output


@pytest.mark.parametrize("in_workspace", [True, False])
def test_scaffold_component_no_params_success(in_workspace: bool) -> None:
    with (
        ProxyRunner.test() as runner,
        isolated_example_project_foo_bar(runner, in_workspace),
    ):
        result = runner.invoke(
            "scaffold",
            "component",
            "dagster_test.components.AllMetadataEmptyComponent",
            "qux",
        )
        assert_runner_result(result)
        assert Path("foo_bar/defs/qux").exists()
        component_yaml_path = Path("foo_bar/defs/qux/component.yaml")
        assert component_yaml_path.exists()
        assert (
            "type: dagster_test.components.AllMetadataEmptyComponent"
            in component_yaml_path.read_text()
        )


@pytest.mark.parametrize("in_workspace", [True, False])
def test_scaffold_component_json_params_success(in_workspace: bool) -> None:
    with (
        ProxyRunner.test() as runner,
        isolated_example_project_foo_bar(runner, in_workspace),
    ):
        result = runner.invoke(
            "scaffold",
            "component",
            "dagster_test.components.SimplePipesScriptComponent",
            "qux",
            "--json-params",
            '{"asset_key": "foo", "filename": "hello.py"}',
        )
        assert_runner_result(result)
        assert Path("foo_bar/defs/qux").exists()
        assert Path("foo_bar/defs/qux/hello.py").exists()
        component_yaml_path = Path("foo_bar/defs/qux/component.yaml")
        assert component_yaml_path.exists()
        assert (
            "type: dagster_test.components.SimplePipesScriptComponent"
            in component_yaml_path.read_text()
        )


@pytest.mark.parametrize("in_workspace", [True, False])
def test_scaffold_component_key_value_params_success(in_workspace: bool) -> None:
    with (
        ProxyRunner.test() as runner,
        isolated_example_project_foo_bar(runner, in_workspace),
    ):
        result = runner.invoke(
            "scaffold",
            "component",
            "dagster_test.components.SimplePipesScriptComponent",
            "qux",
            "--asset-key=foo",
            "--filename=hello.py",
        )
        assert_runner_result(result)
        assert Path("foo_bar/defs/qux").exists()
        assert Path("foo_bar/defs/qux/hello.py").exists()
        component_yaml_path = Path("foo_bar/defs/qux/component.yaml")
        assert component_yaml_path.exists()
        assert (
            "type: dagster_test.components.SimplePipesScriptComponent"
            in component_yaml_path.read_text()
        )


def test_scaffold_component_json_params_and_key_value_params_fails() -> None:
    with ProxyRunner.test() as runner, isolated_example_project_foo_bar(runner):
        result = runner.invoke(
            "scaffold",
            "component",
            "dagster_test.components.SimplePipesScriptComponent",
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
    with ProxyRunner.test() as runner, isolated_example_project_foo_bar(runner):
        result = runner.invoke("scaffold", "component", "fake.Fake", "qux")
        assert_runner_result(result, exit_0=False)
        assert "No component type `fake.Fake` is registered" in result.output


def test_scaffold_component_command_with_non_matching_module_name():
    with ProxyRunner.test() as runner, isolated_example_project_foo_bar(runner):
        #  move the module from foo_bar to module_not_same_as_project
        python_module = Path("foo_bar")
        python_module.rename("module_not_same_as_project")

        result = runner.invoke(
            "scaffold",
            "component",
            "dagster_test.components.AllMetadataEmptyComponent",
            "qux",
        )
        assert_runner_result(result, exit_0=False)
        assert "Cannot find module `foo_bar.lib`" in str(result.exception)


@pytest.mark.parametrize("in_workspace", [True, False])
def test_scaffold_component_already_exists_fails(in_workspace: bool) -> None:
    with (
        ProxyRunner.test() as runner,
        isolated_example_project_foo_bar(runner, in_workspace),
    ):
        result = runner.invoke(
            "scaffold",
            "component",
            "dagster_test.components.AllMetadataEmptyComponent",
            "qux",
        )
        assert_runner_result(result)
        result = runner.invoke(
            "scaffold",
            "component",
            "dagster_test.components.AllMetadataEmptyComponent",
            "qux",
        )
        assert_runner_result(result, exit_0=False)
        assert "already exists" in result.output


def test_scaffold_component_succeeds_non_default_component_package() -> None:
    with ProxyRunner.test() as runner, isolated_example_project_foo_bar(runner):
        alt_lib_path = Path("foo_bar/_defs")
        alt_lib_path.mkdir(parents=True)
        with modify_pyproject_toml() as toml:
            set_toml_value(toml, ("tool", "dg", "project", "components_module"), "foo_bar._defs")
        result = runner.invoke(
            "scaffold",
            "component",
            "dagster_test.components.AllMetadataEmptyComponent",
            "qux",
        )
        assert_runner_result(result)
        assert Path("foo_bar/_defs/qux").exists()
        component_yaml_path = Path("foo_bar/_defs/qux/component.yaml")
        assert component_yaml_path.exists()
        assert (
            "type: dagster_test.components.AllMetadataEmptyComponent"
            in component_yaml_path.read_text()
        )


def test_scaffold_component_fails_components_package_does_not_exist() -> None:
    with ProxyRunner.test() as runner, isolated_example_project_foo_bar(runner):
        with modify_pyproject_toml() as toml:
            set_toml_value(toml, ("tool", "dg", "project", "components_module"), "foo_bar._defs")
        result = runner.invoke(
            "scaffold",
            "component",
            "dagster_test.components.AllMetadataEmptyComponent",
            "qux",
        )
        assert_runner_result(result, exit_0=False)
        assert "Cannot find module `foo_bar._defs`" in str(result.exception)


def test_scaffold_component_succeeds_scaffolded_component_type() -> None:
    with (
        ProxyRunner.test(use_entry_points=True) as runner,
        isolated_example_project_foo_bar(runner),
    ):
        result = runner.invoke("scaffold", "component-type", "Baz")
        assert_runner_result(result)
        assert Path("foo_bar/lib/baz.py").exists()

        result = runner.invoke("scaffold", "component", "foo_bar.lib.Baz", "qux")
        assert_runner_result(result)
        assert Path("foo_bar/defs/qux").exists()
        component_yaml_path = Path("foo_bar/defs/qux/component.yaml")
        assert component_yaml_path.exists()
        assert "type: foo_bar.lib.Baz" in component_yaml_path.read_text()


# ##### REAL COMPONENTS


dbt_project_path = Path("../stub_projects/dbt_project_location/defs/jaffle_shop")


@pytest.mark.parametrize(
    "params",
    [
        ["--json-params", json.dumps({"project_path": str(dbt_project_path)})],
        ["--project-path", str(dbt_project_path)],
    ],
)
def test_scaffold_dbt_project_instance(params) -> None:
    with (
        ProxyRunner.test(use_entry_points=True) as runner,
        isolated_example_project_foo_bar(runner),
    ):
        # We need to add dagster-dbt also because we are using editable installs. Only
        # direct dependencies will be resolved by uv.tool.sources.
        subprocess.run(["uv", "add", "dagster-components[dbt]", "dagster-dbt"], check=True)
        result = runner.invoke(
            "scaffold",
            "component",
            "dagster_components.dagster_dbt.DbtProjectComponent",
            "my_project",
            *params,
        )
        assert_runner_result(result)
        assert Path("foo_bar/defs/my_project").exists()

        component_yaml_path = Path("foo_bar/defs/my_project/component.yaml")
        assert component_yaml_path.exists()
        assert (
            "type: dagster_components.dagster_dbt.DbtProjectComponent"
            in component_yaml_path.read_text()
        )
        assert (
            cross_platfrom_string_path("stub_projects/dbt_project_location/defs/jaffle_shop")
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
        result = runner.invoke("scaffold", "component-type", "Baz")
        assert_runner_result(result)
        assert Path("foo_bar/lib/baz.py").exists()
        dg_context = DgContext.from_file_discovery_and_command_line_config(Path.cwd(), {})
        registry = RemoteComponentRegistry.from_dg_context(dg_context)
        assert registry.has(ComponentKey(name="Baz", namespace="foo_bar.lib"))


def test_scaffold_component_type_already_exists_fails() -> None:
    with (
        ProxyRunner.test(use_entry_points=True) as runner,
        isolated_example_component_library_foo_bar(runner),
    ):
        result = runner.invoke("scaffold", "component-type", "Baz")
        assert_runner_result(result)
        result = runner.invoke("scaffold", "component-type", "Baz")
        assert_runner_result(result, exit_0=False)
        assert "already exists" in result.output


def test_scaffold_component_type_succeeds_non_default_component_lib_package() -> None:
    with (
        ProxyRunner.test(use_entry_points=True) as runner,
        isolated_example_component_library_foo_bar(runner, lib_module_name="foo_bar._lib"),
    ):
        result = runner.invoke(
            "scaffold",
            "component-type",
            "Baz",
        )
        assert_runner_result(result)
        assert Path("foo_bar/_lib/baz.py").exists()
        dg_context = DgContext.from_file_discovery_and_command_line_config(Path.cwd(), {})
        registry = RemoteComponentRegistry.from_dg_context(dg_context)
        assert registry.has(ComponentKey(name="Baz", namespace="foo_bar._lib"))


def test_scaffold_component_type_fails_components_lib_package_does_not_exist(capfd) -> None:
    with (
        ProxyRunner.test(use_entry_points=True) as runner,
        isolated_example_component_library_foo_bar(runner, lib_module_name="foo_bar.fake"),
    ):
        # Delete the entry point module
        shutil.rmtree("foo_bar/fake")

        # An entry point load error will occur before we even get to component type scaffolding
        # code, because the entry points are loaded first.
        result = runner.invoke(
            "scaffold",
            "component-type",
            "Baz",
        )
        assert_runner_result(result, exit_0=False)

        captured = capfd.readouterr()
        assert "Error loading entry point `foo_bar` in group `dagster.components`." in captured.err
