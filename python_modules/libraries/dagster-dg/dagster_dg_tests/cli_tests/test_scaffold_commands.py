import json
import os
import shutil
import subprocess
import textwrap
from pathlib import Path
from typing import Any, Literal, Optional, get_args

import dagster_shared.check as check
import pytest
import tomlkit
from dagster_dg.cli.shared_options import DEFAULT_EDITABLE_DAGSTER_PROJECTS_ENV_VAR
from dagster_dg.component import RemotePluginRegistry
from dagster_dg.context import DgContext
from dagster_dg.utils import (
    create_toml_node,
    cross_platfrom_string_path,
    discover_git_root,
    ensure_dagster_dg_tests_import,
    get_toml_node,
    has_toml_node,
    modify_toml_as_dict,
    pushd,
)
from dagster_shared.serdes.objects import PluginObjectKey
from dagster_shared.serdes.objects.package_entry import json_for_all_components
from typing_extensions import TypeAlias

ensure_dagster_dg_tests_import()

from dagster_dg.scaffold import MIN_DAGSTER_SCAFFOLD_PROJECT_ROOT_OPTION_VERSION
from dagster_dg.utils import ensure_dagster_dg_tests_import
from dagster_shared.libraries import increment_micro_version

from dagster_dg_tests.utils import (
    ProxyRunner,
    assert_runner_result,
    clear_module_from_cache,
    isolated_example_component_library_foo_bar,
    isolated_example_project_foo_bar,
    isolated_example_workspace,
    standardize_box_characters,
)

# ########################
# ##### WORKSPACE
# ########################


@pytest.mark.parametrize(
    "cli_args",
    [
        tuple(),
        ("helloworld",),
        (".",),
    ],
    ids=[
        "no_args",
        "with_name",
        "with_cwd",
    ],
)
def test_scaffold_workspace_command_success(monkeypatch, cli_args: tuple[str, ...]) -> None:
    with ProxyRunner.test() as runner, runner.isolated_filesystem():
        if "." in cli_args:
            os.mkdir("helloworld")
            os.chdir("helloworld")
            expected_name = "helloworld"
        elif "helloworld" in cli_args:
            expected_name = "helloworld"
        else:
            expected_name = "dagster-workspace"

        result = runner.invoke("scaffold", "workspace", *cli_args)
        assert_runner_result(result)

        if "." in cli_args:
            os.chdir("..")

        assert Path(expected_name).exists()
        assert Path(f"{expected_name}/dg.toml").exists()
        assert Path(f"{expected_name}/projects").exists()


def test_scaffold_workspace_already_exists_failure(monkeypatch) -> None:
    dagster_git_repo_dir = discover_git_root(Path(__file__))
    monkeypatch.setenv("DAGSTER_GIT_REPO_DIR", str(dagster_git_repo_dir))

    with ProxyRunner.test() as runner, runner.isolated_filesystem():
        os.mkdir("dagster-workspace")
        result = runner.invoke(
            "scaffold",
            "workspace",
            "--use-editable-dagster",
            "dagster-workspace",
        )
        assert_runner_result(result, exit_0=False)
        assert "already exists" in result.output


# ########################
# ##### PROJECT
# ########################

# At this time all of our tests are against an editable install of dagster. The reason
# for this is that this package should always be tested against the corresponding version of
# dagster (i.e. from the same commit), and the only way to achieve this right now is
# using the editable install variant of `dg scaffold project`.
#
# Ideally we would have a way to still use the matching dagster-components without using the
# editable install variant, but this will require somehow configuring uv to ensure that it builds
# and returns the local version of the package.


@pytest.mark.parametrize(
    "cli_args,input_str,opts",
    [
        (("--", "."), "y\n", {}),
        # Test preexisting venv in the project directory
        (("--", "."), None, {"use_preexisting_venv": True}),
        # Skip the uv sync prompt and automatically uv sync
        (("--uv-sync", "--", "."), None, {}),
        # Skip the uv sync prompt and don't uv sync
        (("--no-uv-sync", "--", "."), None, {}),
        # Test uv not available. When uv is not available there will be no prompt-- so this test
        # will hang if it's not working because we don't provide an input string.
        (("--", "."), None, {"no_uv": True}),
        (("--", "foo-bar"), "y\n", {}),
        # Test declining to create a venv
        (("--", "foo-bar"), "n\n", {}),
    ],
    ids=[
        "dirname_cwd",
        "dirname_cwd_preexisting_venv",
        "dirname_cwd_explicit_uv_sync",
        "dirname_cwd_explicit_no_uv_sync",
        "dirname_cwd_no_uv",
        "dirname_arg",
        "dirname_arg_no_venv",
    ],
)
# def test_scaffold_project_outside_workspace_success(monkeypatch) -> None:
def test_scaffold_project_success(
    monkeypatch, cli_args: tuple[str, ...], input_str: Optional[str], opts: dict[str, object]
) -> None:
    use_preexisting_venv = check.opt_bool_elem(opts, "use_preexisting_venv") or False
    no_uv = check.opt_bool_elem(opts, "no_uv") or False
    # Remove when we are able to test without editable install
    dagster_git_repo_dir = discover_git_root(Path(__file__))
    monkeypatch.setenv("DAGSTER_GIT_REPO_DIR", str(dagster_git_repo_dir))
    if no_uv:
        monkeypatch.setattr("dagster_dg.cli.scaffold.is_uv_installed", lambda: False)
    with ProxyRunner.test() as runner, runner.isolated_filesystem(), clear_module_from_cache("bar"):
        if "." in cli_args:  # creating in CWD
            os.mkdir("foo-bar")
            os.chdir("foo-bar")
            if use_preexisting_venv:
                subprocess.run(["uv", "venv"], check=True)

        # result = runner.invoke("scaffold", "project", "foo-bar", "--use-editable-dagster")
        result = runner.invoke(
            "scaffold", "project", "--use-editable-dagster", *cli_args, input=input_str
        )
        assert_runner_result(result)

        if "." in cli_args:  # creating in CWD
            os.chdir("..")

        assert Path("foo-bar").exists()
        assert Path("foo-bar/src/foo_bar").exists()
        assert Path("foo-bar/src/foo_bar/components").exists()
        assert Path("foo-bar/src/foo_bar/defs").exists()
        assert Path("foo-bar/tests").exists()
        assert Path("foo-bar/pyproject.toml").exists()

        # this indicates user opts to create venv and uv.lock
        if not use_preexisting_venv and (
            (input_str and input_str.endswith("y\n")) or "--uv-sync" in cli_args
        ):
            assert Path("foo-bar/.venv").exists()
            assert Path("foo-bar/uv.lock").exists()
        elif use_preexisting_venv:
            assert Path("foo-bar/.venv").exists()
            assert not Path("foo-bar/uv.lock").exists()
        else:
            assert not Path("foo-bar/.venv").exists()
            assert not Path("foo-bar/uv.lock").exists()


def test_scaffold_project_inside_workspace_success(monkeypatch) -> None:
    # Remove when we are able to test without editable install
    dagster_git_repo_dir = discover_git_root(Path(__file__))
    monkeypatch.setenv("DAGSTER_GIT_REPO_DIR", str(dagster_git_repo_dir))

    with ProxyRunner.test() as runner, isolated_example_workspace(runner):
        result = runner.invoke(
            "scaffold",
            "project",
            "projects/foo-bar",
            "--verbose",
            "--uv-sync",
        )
        assert_runner_result(result)
        assert Path("projects/foo-bar").exists()
        assert Path("projects/foo-bar/src/foo_bar").exists()
        assert Path("projects/foo-bar/src/foo_bar/components").exists()
        assert Path("projects/foo-bar/src/foo_bar/defs").exists()
        assert Path("projects/foo-bar/tests").exists()
        assert Path("projects/foo-bar/pyproject.toml").exists()
        assert Path("projects/foo-bar/.gitignore").exists()

        # Check project TOML content
        toml = tomlkit.parse(Path("projects/foo-bar/pyproject.toml").read_text())
        assert get_toml_node(toml, ("tool", "dg", "project", "root_module"), str) == "foo_bar"

        # Check workspace TOML content
        raw_toml = Path("dg.toml").read_text()
        toml = tomlkit.parse(raw_toml)
        assert get_toml_node(toml, ("workspace", "projects", 0, "path"), str) == "projects/foo-bar"

        # Make sure there is an empty line before the new entry
        assert "\n\n[[workspace.projects]]\n" in raw_toml

        # Check venv not created
        assert Path("projects/foo-bar/.venv").exists()
        assert Path("projects/foo-bar/uv.lock").exists()

        # Restore when we are able to test without editable install
        # with open("projects/bar/pyproject.toml") as f:
        #     toml = tomlkit.parse(f.read())
        #
        #     # No tool.uv.sources added without --use-editable-dagster
        #     assert "uv" not in toml["tool"]

        # Populate cache
        with pushd("projects/foo-bar"):
            subprocess.check_output(["uv", "sync"])  # create venv/lock
            result = runner.invoke("list", "plugins", "--verbose")
            assert_runner_result(result)
            assert "CACHE [miss]" in result.output

        # Check cache was populated
        with pushd("projects/foo-bar"):
            result = runner.invoke("list", "plugins", "--verbose")
            assert_runner_result(result)
            assert "CACHE [hit]" in result.output

        # Create another project, make sure it's appended correctly to the workspace TOML and exists
        # in a different directory.
        result = runner.invoke("scaffold", "project", "other_projects/baz", "--verbose")
        assert_runner_result(result)

        # Check workspace TOML content
        raw_toml = Path("dg.toml").read_text()
        toml = tomlkit.parse(raw_toml)
        assert (
            get_toml_node(toml, ("workspace", "projects", 1, "path"), str) == "other_projects/baz"
        )


def test_scaffold_project_inside_workspace_applies_scaffold_project_options(monkeypatch):
    dagster_git_repo_dir = discover_git_root(Path(__file__))
    monkeypatch.setenv("DAGSTER_GIT_REPO_DIR", str(dagster_git_repo_dir))
    with (
        ProxyRunner.test() as runner,
        isolated_example_workspace(runner, use_editable_dagster=False),
    ):
        with modify_toml_as_dict(Path("dg.toml")) as toml_dict:
            create_toml_node(
                toml_dict,
                ("workspace", "scaffold_project_options", "use_editable_dagster"),
                True,
            )

        result = runner.invoke(
            "scaffold",
            "project",
            "projects/foo-bar",
        )
        assert_runner_result(result)
        # Check that use_editable_dagster was applied
        toml = tomlkit.parse(Path("projects/foo-bar/pyproject.toml").read_text())
        assert has_toml_node(toml, ("tool", "uv", "sources", "dagster"))


EditableOption: TypeAlias = Literal["--use-editable-dagster"]


@pytest.mark.parametrize("option", get_args(EditableOption))
@pytest.mark.parametrize("value_source", ["env_var", "arg"])
def test_scaffold_project_editable_dagster_success(
    value_source: str, option: EditableOption, monkeypatch
) -> None:
    dagster_git_repo_dir = discover_git_root(Path(__file__))
    if value_source == "env_var":
        monkeypatch.setenv("DAGSTER_GIT_REPO_DIR", str(dagster_git_repo_dir))
        editable_args = [option, "--"]
    else:
        editable_args = [option, str(dagster_git_repo_dir)]
    with (
        ProxyRunner.test() as runner,
        isolated_example_workspace(runner, use_editable_dagster=False),
    ):
        result = runner.invoke("scaffold", "project", *editable_args, "projects/foo-bar")
        assert_runner_result(result)
        assert Path("projects/foo-bar").exists()
        assert Path("projects/foo-bar/pyproject.toml").exists()
        with open("projects/foo-bar/pyproject.toml") as f:
            toml = tomlkit.parse(f.read())
            validate_pyproject_toml_with_editable(toml, option, dagster_git_repo_dir)


def validate_pyproject_toml_with_editable(
    toml: tomlkit.TOMLDocument,
    option: EditableOption,
    repo_root: Path,
) -> None:
    if option == "--use-editable-dagster":
        assert get_toml_node(toml, ("tool", "uv", "sources", "dagster"), dict) == {
            "path": str(repo_root / "python_modules" / "dagster"),
            "editable": True,
        }
        assert get_toml_node(toml, ("tool", "uv", "sources", "dagster-pipes"), dict) == {
            "path": str(repo_root / "python_modules" / "dagster-pipes"),
            "editable": True,
        }
        assert get_toml_node(toml, ("tool", "uv", "sources", "dagster-shared"), dict) == {
            "path": str(repo_root / "python_modules" / "libraries" / "dagster-shared"),
            "editable": True,
        }
        assert get_toml_node(toml, ("tool", "uv", "sources", "dagster-webserver"), dict) == {
            "path": str(repo_root / "python_modules" / "dagster-webserver"),
            "editable": True,
        }
        # Check for presence of one random package with no component to ensure we are
        # preemptively adding all packages
        assert get_toml_node(toml, ("tool", "uv", "sources", "dagstermill"), dict) == {
            "path": str(repo_root / "python_modules" / "libraries" / "dagstermill"),
            "editable": True,
        }
    else:
        assert not has_toml_node(toml, ("tool", "uv", "sources", "dagster"))
        assert not has_toml_node(toml, ("tool", "uv", "sources", "dagster-pipes"))
        assert not has_toml_node(toml, ("tool", "uv", "sources", "dagster-shared"))
        assert not has_toml_node(toml, ("tool", "uv", "sources", "dagster-webserver"))
        assert not has_toml_node(toml, ("tool", "uv", "sources", "dagstermill"))


def test_scaffold_project_use_editable_dagster_env_var_succeeds(monkeypatch) -> None:
    dagster_git_repo_dir = discover_git_root(Path(__file__))
    monkeypatch.setenv("DAGSTER_GIT_REPO_DIR", str(dagster_git_repo_dir))
    monkeypatch.setenv(DEFAULT_EDITABLE_DAGSTER_PROJECTS_ENV_VAR, "1")
    with ProxyRunner.test() as runner, runner.isolated_filesystem():
        # We need to use subprocess rather than runner here because the environment variable affects
        # CLI defaults set at process startup.
        subprocess.check_output(["dg", "scaffold", "project", "--uv-sync", "foo-bar"], text=True)
        with open("foo-bar/pyproject.toml") as f:
            toml = tomlkit.parse(f.read())
            validate_pyproject_toml_with_editable(
                toml, "--use-editable-dagster", dagster_git_repo_dir
            )


def test_scaffold_project_no_populate_cache_success(monkeypatch) -> None:
    dagster_git_repo_dir = discover_git_root(Path(__file__))
    monkeypatch.setenv("DAGSTER_GIT_REPO_DIR", str(dagster_git_repo_dir))
    with ProxyRunner.test() as runner, runner.isolated_filesystem():
        result = runner.invoke(
            "scaffold",
            "project",
            "foo-bar",
            "--no-populate-cache",
            "--python-environment",
            "uv_managed",
            "--use-editable-dagster",
        )
        assert_runner_result(result)
        assert Path("foo-bar").exists()
        assert Path("foo-bar/src/foo_bar").exists()
        assert Path("foo-bar/src/foo_bar/components").exists()
        assert Path("foo-bar/src/foo_bar/defs").exists()
        assert Path("foo-bar/tests").exists()
        assert Path("foo-bar/pyproject.toml").exists()

        # Check venv created
        assert Path("foo-bar/.venv").exists()
        assert Path("foo-bar/uv.lock").exists()

        with pushd("foo-bar"):
            result = runner.invoke("list", "plugins", "--verbose")
            assert_runner_result(result)
            assert "CACHE [miss]" in result.output


def test_scaffold_project_python_environment_uv_managed_success(monkeypatch) -> None:
    dagster_git_repo_dir = discover_git_root(Path(__file__))
    monkeypatch.setenv("DAGSTER_GIT_REPO_DIR", str(dagster_git_repo_dir))
    with ProxyRunner.test() as runner, runner.isolated_filesystem():
        result = runner.invoke(
            "scaffold",
            "project",
            "foo-bar",
            "--python-environment",
            "uv_managed",
            "--use-editable-dagster",
        )
        assert_runner_result(result)
        assert Path("foo-bar").exists()
        assert Path("foo-bar/src/foo_bar").exists()
        assert Path("foo-bar/src/foo_bar/components").exists()
        assert Path("foo-bar/src/foo_bar/defs").exists()
        assert Path("foo-bar/tests").exists()
        assert Path("foo-bar/pyproject.toml").exists()

        # Check venv not created
        assert Path("foo-bar/.venv").exists()
        assert Path("foo-bar/uv.lock").exists()


@pytest.mark.parametrize("option", get_args(EditableOption))
def test_scaffold_project_editable_dagster_no_env_var_no_value_fails(
    option: EditableOption, monkeypatch
) -> None:
    monkeypatch.setenv("DAGSTER_GIT_REPO_DIR", "")
    with (
        ProxyRunner.test() as runner,
        isolated_example_workspace(runner, use_editable_dagster=False),
    ):
        result = runner.invoke("scaffold", "project", option, "--", "bar")
        assert_runner_result(result, exit_0=False)
        assert "requires the `DAGSTER_GIT_REPO_DIR`" in result.output


def test_scaffold_project_already_exists_fails() -> None:
    with ProxyRunner.test() as runner, isolated_example_workspace(runner):
        result = runner.invoke("scaffold", "project", "bar")
        assert_runner_result(result)
        result = runner.invoke("scaffold", "project", "bar")
        assert_runner_result(result, exit_0=False)
        assert "already specifies a project at" in result.output


def test_scaffold_project_non_editable_dagster_dagster_components_executable_exists() -> None:
    with ProxyRunner.test() as runner, runner.isolated_filesystem():
        result = runner.invoke("scaffold", "project", "bar", "--python-environment", "uv_managed")
        assert_runner_result(result)
        with pushd("bar"):
            result = runner.invoke("list", "plugins", "--verbose")
            assert_runner_result(result)


# ########################
# ##### COMPONENT
# ########################


def test_scaffold_component_dynamic_subcommand_generation() -> None:
    with (
        ProxyRunner.test(use_fixed_test_components=True) as runner,
        isolated_example_project_foo_bar(runner),
    ):
        result = runner.invoke("scaffold", "--help")
        assert_runner_result(result)

        normalized_output = standardize_box_characters(result.output)
        # These are wrapped in a table so it's hard to check exact output.
        for line in [
            "╭─ Commands",
            "│ project",
            "│ dagster_test.components.AllMetadataEmptyComponent",
            "│ dagster_test.components.ComplexAssetComponent",
            "│ dagster_test.components.SimpleAssetComponent",
            "│ dagster_test.components.SimplePipesScriptComponent",
        ]:
            assert standardize_box_characters(line) in normalized_output


@pytest.mark.parametrize("in_workspace", [True, False])
def test_scaffold_component_no_params_success(in_workspace: bool) -> None:
    with (
        ProxyRunner.test(use_fixed_test_components=True) as runner,
        isolated_example_project_foo_bar(runner, in_workspace),
    ):
        result = runner.invoke(
            "scaffold", "dagster_test.components.AllMetadataEmptyComponent", "qux"
        )
        assert_runner_result(result)
        assert Path("src/foo_bar/defs/qux").exists()
        component_yaml_path = Path("src/foo_bar/defs/qux/component.yaml")
        assert component_yaml_path.exists()
        assert (
            "type: dagster_test.components.AllMetadataEmptyComponent"
            in component_yaml_path.read_text()
        )


@pytest.mark.parametrize("in_workspace", [True, False])
def test_scaffold_component_json_params_success(in_workspace: bool) -> None:
    with (
        ProxyRunner.test(use_fixed_test_components=True) as runner,
        isolated_example_project_foo_bar(runner, in_workspace),
    ):
        result = runner.invoke(
            "scaffold",
            "dagster_test.components.SimplePipesScriptComponent",
            "qux",
            "--json-params",
            '{"asset_key": "foo", "filename": "hello.py"}',
        )
        assert_runner_result(result)
        assert Path("src/foo_bar/defs/qux").exists()
        assert Path("src/foo_bar/defs/qux/hello.py").exists()
        component_yaml_path = Path("src/foo_bar/defs/qux/component.yaml")
        assert component_yaml_path.exists()
        assert (
            "type: dagster_test.components.SimplePipesScriptComponent"
            in component_yaml_path.read_text()
        )


@pytest.mark.parametrize("in_workspace", [True, False])
def test_scaffold_component_key_value_params_success(in_workspace: bool) -> None:
    with (
        ProxyRunner.test(use_fixed_test_components=True) as runner,
        isolated_example_project_foo_bar(runner, in_workspace),
    ):
        result = runner.invoke(
            "scaffold",
            "dagster_test.components.SimplePipesScriptComponent",
            "qux",
            "--asset-key=foo",
            "--filename=hello.py",
        )
        assert_runner_result(result)
        assert Path("src/foo_bar/defs/qux").exists()
        assert Path("src/foo_bar/defs/qux/hello.py").exists()
        component_yaml_path = Path("src/foo_bar/defs/qux/component.yaml")
        assert component_yaml_path.exists()
        assert (
            "type: dagster_test.components.SimplePipesScriptComponent"
            in component_yaml_path.read_text()
        )


def test_scaffold_component_json_params_and_key_value_params_fails() -> None:
    with (
        ProxyRunner.test(use_fixed_test_components=True) as runner,
        isolated_example_project_foo_bar(runner),
    ):
        result = runner.invoke(
            "scaffold",
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
        result = runner.invoke("scaffold", "fake.Fake", "qux")
        assert_runner_result(result, exit_0=False)
        assert "No plugin object `fake.Fake` is registered" in result.output


def test_scaffold_component_command_with_non_matching_module_name():
    with (
        ProxyRunner.test(use_fixed_test_components=True) as runner,
        isolated_example_project_foo_bar(runner),
    ):
        #  move the module from foo_bar to module_not_same_as_project
        python_module = Path("src/foo_bar")
        python_module.rename("module_not_same_as_project")

        result = runner.invoke(
            "scaffold", "dagster_test.components.AllMetadataEmptyComponent", "qux"
        )
        assert_runner_result(result, exit_0=False)
        assert "Cannot find module `foo_bar" in result.output


@pytest.mark.parametrize("in_workspace", [True, False])
def test_scaffold_component_already_exists_fails(in_workspace: bool) -> None:
    with (
        ProxyRunner.test(use_fixed_test_components=True) as runner,
        isolated_example_project_foo_bar(runner, in_workspace),
    ):
        result = runner.invoke(
            "scaffold", "dagster_test.components.AllMetadataEmptyComponent", "qux"
        )
        assert_runner_result(result)
        result = runner.invoke(
            "scaffold", "dagster_test.components.AllMetadataEmptyComponent", "qux"
        )
        assert_runner_result(result, exit_0=False)
        assert "already exists" in result.output


def test_scaffold_component_succeeds_non_default_defs_module() -> None:
    with (
        ProxyRunner.test(use_fixed_test_components=True) as runner,
        isolated_example_project_foo_bar(runner),
    ):
        alt_defs_path = Path("src/foo_bar/_defs")
        alt_defs_path.mkdir(parents=True)
        with modify_toml_as_dict(Path("pyproject.toml")) as toml_dict:
            create_toml_node(toml_dict, ("tool", "dg", "project", "defs_module"), "foo_bar._defs")
        result = runner.invoke(
            "scaffold", "dagster_test.components.AllMetadataEmptyComponent", "qux"
        )
        assert_runner_result(result)
        assert Path("src/foo_bar/_defs/qux").exists()
        component_yaml_path = Path("src/foo_bar/_defs/qux/component.yaml")
        assert component_yaml_path.exists()
        assert (
            "type: dagster_test.components.AllMetadataEmptyComponent"
            in component_yaml_path.read_text()
        )


def test_scaffold_component_fails_defs_module_does_not_exist() -> None:
    with (
        ProxyRunner.test(use_fixed_test_components=True) as runner,
        isolated_example_project_foo_bar(runner),
    ):
        with modify_toml_as_dict(Path("pyproject.toml")) as toml_dict:
            create_toml_node(toml_dict, ("tool", "dg", "project", "defs_module"), "foo_bar._defs")
        result = runner.invoke(
            "scaffold", "dagster_test.components.AllMetadataEmptyComponent", "qux"
        )
        assert_runner_result(result, exit_0=False)
        assert "Cannot find module `foo_bar._defs`" in result.output


def test_scaffold_component_succeeds_scaffolded_component_type() -> None:
    with (
        ProxyRunner.test() as runner,
        isolated_example_project_foo_bar(
            runner,
            # plugins not discoverable in process due to not doing a proper install
            python_environment="uv_managed",
        ),
    ):
        result = runner.invoke("scaffold", "component-type", "Baz")
        assert_runner_result(result)
        assert Path("src/foo_bar/components/baz.py").exists()

        result = runner.invoke("scaffold", "foo_bar.components.Baz", "qux")
        assert_runner_result(result)
        assert Path("src/foo_bar/defs/qux").exists()
        component_yaml_path = Path("src/foo_bar/defs/qux/component.yaml")
        assert component_yaml_path.exists()
        assert "type: foo_bar.components.Baz" in component_yaml_path.read_text()


def test_scaffold_component_succeeds_scaffolded_no_model() -> None:
    with (
        ProxyRunner.test() as runner,
        isolated_example_project_foo_bar(runner),
    ):
        result = runner.invoke("scaffold", "component-type", "Baz", "--no-model")
        assert_runner_result(result)
        assert Path("src/foo_bar/components/baz.py").exists()

        output = '''import dagster as dg
from dagster.components import Component, ComponentLoadContext, Resolvable


class Baz(Component, Resolvable):
    """COMPONENT SUMMARY HERE.

    COMPONENT DESCRIPTION HERE.
    """

    def __init__(
        self,
        # added arguments here will define yaml schema via Resolvable
    ):
        pass

    def build_defs(self, context: ComponentLoadContext) -> dg.Definitions:
        # Add definition construction logic here.
        return dg.Definitions()
'''

        assert Path("src/foo_bar/components/baz.py").read_text() == output


# ##### SHIMS


def test_scaffold_asset() -> None:
    with (
        ProxyRunner.test() as runner,
        isolated_example_project_foo_bar(runner),
    ):
        result = runner.invoke("scaffold", "dagster.asset", "assets/foo.py")
        assert_runner_result(result)
        assert Path("src/foo_bar/defs/assets/foo.py").exists()
        assert Path("src/foo_bar/defs/assets/foo.py").read_text().startswith("import dagster as dg")
        assert not Path("src/foo_bar/defs/assets/foo.py").is_dir()
        assert not Path("src/foo_bar/defs/assets/component.yaml").exists()

        result = runner.invoke("scaffold", "dagster.asset", "assets/bar.py")
        assert_runner_result(result)
        assert Path("src/foo_bar/defs/assets/bar.py").exists()
        assert not Path("src/foo_bar/defs/assets/component.yaml").exists()


def test_scaffold_asset_check_with_key() -> None:
    with (
        ProxyRunner.test() as runner,
        isolated_example_project_foo_bar(runner),
    ):
        result = runner.invoke(
            "scaffold", "dagster.asset_check", "asset_checks/my_check.py", "--asset-key=my/key"
        )
        assert_runner_result(result)
        assert Path("src/foo_bar/defs/asset_checks/my_check.py").exists()
        # check is uncommented if pointed at an asset
        assert (
            Path("src/foo_bar/defs/asset_checks/my_check.py")
            .read_text()
            .startswith("import dagster as dg")
        )
        assert (
            "asset=dg.AssetKey(['my', 'key'])"
            in Path("src/foo_bar/defs/asset_checks/my_check.py").read_text()
        )
        assert not Path("src/foo_bar/defs/asset_checks/my_check.py").is_dir()
        assert not Path("src/foo_bar/defs/asset_checks/component.yaml").exists()

        result = runner.invoke("list", "defs")
        assert_runner_result(result)
        assert "my_check" in result.output


def test_scaffold_bad_extension() -> None:
    with (
        ProxyRunner.test() as runner,
        isolated_example_project_foo_bar(runner),
    ):
        result = runner.invoke("scaffold", "dagster.asset", "assets/foo")
        assert_runner_result(result, exit_0=False)


def test_scaffold_multi_asset_basic() -> None:
    with (
        ProxyRunner.test() as runner,
        isolated_example_project_foo_bar(runner),
    ):
        result = runner.invoke("scaffold", "dagster.multi_asset", "multi_assets/composite.py")
        assert_runner_result(result)
        assert Path("src/foo_bar/defs/multi_assets/composite.py").exists()
        assert (
            Path("src/foo_bar/defs/multi_assets/composite.py")
            .read_text()
            .startswith("import dagster as dg")
        )
        assert "@dg.multi_asset" in Path("src/foo_bar/defs/multi_assets/composite.py").read_text()
        asset_content = Path("src/foo_bar/defs/multi_assets/composite.py").read_text()
        assert "dg.AssetSpec(key=dg.AssetKey(['composite', 'first_asset']))" in asset_content
        assert "dg.AssetSpec(key=dg.AssetKey(['composite', 'second_asset']))" in asset_content
        assert not Path("src/foo_bar/defs/multi_assets/composite.py").is_dir()
        assert not Path("src/foo_bar/defs/multi_assets/component.yaml").exists()

        result = runner.invoke("list", "defs")
        assert_runner_result(result)
        output = result.output
        assert "composite/first_asset" in output
        assert "composite/second_asset" in output


def test_scaffold_multi_asset_params() -> None:
    with (
        ProxyRunner.test() as runner,
        isolated_example_project_foo_bar(runner),
    ):
        # First, try scaffolding with multiple options using --asset-key
        result = runner.invoke(
            "scaffold",
            "dagster.multi_asset",
            "multi_assets/custom_keys.py",
            "--asset-key",
            "orders",
            "--asset-key",
            "customers",
        )
        assert_runner_result(result)
        assert Path("src/foo_bar/defs/multi_assets/custom_keys.py").exists()
        asset_content = Path("src/foo_bar/defs/multi_assets/custom_keys.py").read_text()
        assert "dg.AssetSpec(key=dg.AssetKey(['orders']))" in asset_content
        assert "dg.AssetSpec(key=dg.AssetKey(['customers']))" in asset_content

        result = runner.invoke("list", "defs")
        assert_runner_result(result)
        output = result.output
        assert "orders" in output
        assert "customers" in output

        # Next, try more complex keys with --json-params
        result = runner.invoke(
            "scaffold",
            "dagster.multi_asset",
            "multi_assets/with_nested_keys.py",
            "--json-params",
            '{"asset_key": ["foo/bar", "baz/qux"]}',
        )
        assert_runner_result(result)
        assert Path("src/foo_bar/defs/multi_assets/with_nested_keys.py").exists()
        asset_content = Path("src/foo_bar/defs/multi_assets/with_nested_keys.py").read_text()
        assert "dg.AssetSpec(key=dg.AssetKey(['foo', 'bar']))" in asset_content
        assert "dg.AssetSpec(key=dg.AssetKey(['baz', 'qux']))" in asset_content

        result = runner.invoke("list", "defs")
        assert_runner_result(result)
        output = result.output
        assert "foo/bar" in output
        assert "baz/qux" in output


def test_scaffold_job() -> None:
    with (
        ProxyRunner.test() as runner,
        isolated_example_project_foo_bar(runner),
    ):
        result = runner.invoke("scaffold", "dagster.job", "jobs/my_pipeline.py")
        assert_runner_result(result)
        assert Path("src/foo_bar/defs/jobs/my_pipeline.py").exists()
        assert (
            Path("src/foo_bar/defs/jobs/my_pipeline.py")
            .read_text()
            .startswith("import dagster as dg")
        )
        assert "@dg.job" in Path("src/foo_bar/defs/jobs/my_pipeline.py").read_text()
        job_content = Path("src/foo_bar/defs/jobs/my_pipeline.py").read_text()
        # Check for simple job scaffolding
        assert "pass" in job_content
        assert not Path("src/foo_bar/defs/jobs/my_pipeline.py").is_dir()
        assert not Path("src/foo_bar/defs/jobs/component.yaml").exists()

        # Create another job file to verify it works consistently
        result = runner.invoke("scaffold", "dagster.job", "jobs/another_job.py")
        assert_runner_result(result)
        assert Path("src/foo_bar/defs/jobs/another_job.py").exists()


def test_scaffold_sensor() -> None:
    with (
        ProxyRunner.test() as runner,
        isolated_example_project_foo_bar(runner),
    ):
        result = runner.invoke("scaffold", "dagster.sensor", "my_sensor.py")
        assert_runner_result(result)
        assert Path("src/foo_bar/defs/my_sensor.py").exists()
        assert not Path("src/foo_bar/defs/component.yaml").exists()


# ##### REAL COMPONENTS


dbt_project_path = Path("../stub_projects/dbt_project_location/defs/jaffle_shop")


@pytest.mark.parametrize(
    "params",
    [
        ["--json-params", json.dumps({"project_path": str(dbt_project_path)})],
        ["--project-path", str(dbt_project_path)],
    ],
)
@pytest.mark.parametrize(
    "dagster_version",
    [
        "editable",  # most recent
        increment_micro_version(MIN_DAGSTER_SCAFFOLD_PROJECT_ROOT_OPTION_VERSION, -1),
    ],
    ids=str,
)
def test_scaffold_dbt_project_instance(params, dagster_version) -> None:
    project_kwargs: dict[str, Any] = (
        {"use_editable_dagster": True}
        if dagster_version == "editable"
        else {
            "use_editable_dagster": False,
            "dagster_version": dagster_version,
        }
    )

    with (
        ProxyRunner.test() as runner,
        isolated_example_project_foo_bar(runner, python_environment="uv_managed", **project_kwargs),
    ):
        # We need to add dagster-dbt also because we are using editable installs. Only
        # direct dependencies will be resolved by uv.tool.sources.
        subprocess.run(["uv", "add", "dagster-dbt"], check=True)
        result = runner.invoke("scaffold", "dagster_dbt.DbtProjectComponent", "my_project", *params)
        assert_runner_result(result)
        assert Path("src/foo_bar/defs/my_project").exists()

        component_yaml_path = Path("src/foo_bar/defs/my_project/component.yaml")
        assert component_yaml_path.exists()
        assert "type: dagster_dbt.DbtProjectComponent" in component_yaml_path.read_text()
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
        assert Path("src/foo_bar/components/baz.py").exists()
        dg_context = DgContext.from_file_discovery_and_command_line_config(Path.cwd(), {})
        registry = RemotePluginRegistry.from_dg_context(dg_context)
        assert registry.has(PluginObjectKey(name="Baz", namespace="foo_bar.components"))
        assert Path("src/foo_bar/components/__init__.py").read_text() == textwrap.dedent("""
            from foo_bar.components.baz import Baz as Baz
        """)

        # ensure even fresh components with no schema show up in docs
        blobs = json_for_all_components([v for _, v in registry.items()])
        component_names = []
        for blob in blobs:
            component_names.extend(b["name"] for b in blob["componentTypes"])
        assert "foo_bar.components.Baz" in component_names


def test_scaffold_component_type_already_exists_fails() -> None:
    with (
        ProxyRunner.test() as runner,
        isolated_example_component_library_foo_bar(runner),
    ):
        result = runner.invoke("scaffold", "component-type", "Baz")
        assert_runner_result(result)
        result = runner.invoke("scaffold", "component-type", "Baz")
        assert_runner_result(result, exit_0=False)
        assert "already exists" in result.output


def test_scaffold_component_type_succeeds_non_default_component_components_package() -> None:
    with (
        ProxyRunner.test() as runner,
        isolated_example_component_library_foo_bar(
            runner, components_module_name="foo_bar._components"
        ),
    ):
        result = runner.invoke("scaffold", "component-type", "Baz")
        assert_runner_result(result)
        assert Path("src/foo_bar/_components/baz.py").exists()
        dg_context = DgContext.from_file_discovery_and_command_line_config(Path.cwd(), {})
        registry = RemotePluginRegistry.from_dg_context(dg_context)
        assert registry.has(PluginObjectKey(name="Baz", namespace="foo_bar._components"))


def test_scaffold_component_type_fails_components_lib_package_does_not_exist(capfd) -> None:
    with (
        ProxyRunner.test() as runner,
        isolated_example_component_library_foo_bar(runner, components_module_name="foo_bar.fake"),
    ):
        # Delete the entry point module
        shutil.rmtree("src/foo_bar/fake")

        # An entry point load error will occur before we even get to component type scaffolding
        # code, because the entry points are loaded first.
        result = runner.invoke("scaffold", "component-type", "Baz")
        assert_runner_result(result, exit_0=False)
        assert "Cannot find module `foo_bar.fake`" in result.output
