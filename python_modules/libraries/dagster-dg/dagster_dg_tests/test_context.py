import re
import subprocess
from collections.abc import Sequence
from contextlib import contextmanager
from pathlib import Path
from typing import Any, Union

import pytest
from dagster_dg.config import DgFileConfigDirectoryType, get_type_str
from dagster_dg.context import DgContext
from dagster_dg.error import DgError
from dagster_dg.utils import (
    TomlPath,
    create_toml_node,
    delete_toml_node,
    modify_toml_as_dict,
    pushd,
    toml_path_from_str,
    toml_path_to_str,
)

from dagster_dg_tests.utils import (
    ProxyRunner,
    isolated_components_venv,
    isolated_example_project_foo_bar,
    isolated_example_workspace,
)


def test_context_in_workspace():
    with ProxyRunner.test() as runner, isolated_example_workspace(runner):
        # go into a subdirectory to make sure root resolution works
        path_arg = Path.cwd() / "libraries"

        context = DgContext.for_workspace_environment(path_arg, {})
        assert context.root_path == Path.cwd()
        assert context.workspace_root_path == Path.cwd()

        # Test config properly set
        with modify_toml_as_dict(Path("pyproject.toml")) as toml_dict:
            create_toml_node(toml_dict, ("tool", "dg", "cli", "verbose"), True)
        context = DgContext.for_workspace_environment(path_arg, {})
        assert context.config.cli.verbose is True


def test_context_in_project_in_workspace():
    with ProxyRunner.test() as runner, isolated_example_workspace(runner, project_name="foo-bar"):
        project_path = Path.cwd() / "projects" / "foo-bar"
        # go into a project subdirectory to make sure root resolution works
        path_arg = project_path / "foo_bar_tests"

        context = DgContext.for_project_environment(path_arg, {})
        assert context.root_path == project_path
        assert context.workspace_root_path == Path.cwd()
        assert context.config.cli.verbose is False  # default

        # Test config inheritance from workspace
        with modify_toml_as_dict(Path("pyproject.toml")) as toml_dict:
            create_toml_node(toml_dict, ("tool", "dg", "cli", "verbose"), True)
        context = DgContext.for_project_environment(path_arg, {})
        assert context.config.cli.verbose is True

        # Test cli config in project is ignored and generates warning
        with pushd(project_path), modify_toml_as_dict(Path("pyproject.toml")) as pyproject_toml:
            create_toml_node(pyproject_toml, ("tool", "dg", "cli", "verbose"), False)
        with pytest.warns(match="`tool.dg.cli` section detected in project"):
            context = DgContext.for_project_environment(path_arg, {})
        assert context.config.cli.verbose is True


def test_context_in_project_outside_workspace():
    with ProxyRunner.test() as runner, isolated_example_project_foo_bar(runner, in_workspace=False):
        project_path = Path.cwd()
        # go into a project subdirectory to make sure root resolution works
        path_arg = project_path / "foo_tests"

        context = DgContext.for_project_environment(path_arg, {})
        assert context.root_path == project_path
        assert context.is_workspace is False
        assert context.config.cli.verbose is False

        # Test CLI setting is used in project outside of workspace
        with modify_toml_as_dict(Path("pyproject.toml")) as pyproject_toml:
            create_toml_node(pyproject_toml, ("tool", "dg", "cli", "verbose"), True)
        context = DgContext.for_project_environment(path_arg, {})
        assert context.config.cli.verbose is True


def test_context_outside_project_or_workspace():
    with ProxyRunner.test() as runner, isolated_components_venv(runner):
        context = DgContext.from_file_discovery_and_command_line_config(Path.cwd(), {})
        assert context.root_path == Path.cwd()
        assert context.is_workspace is False
        assert context.config.cli.verbose is False


# ########################
# ##### EXECUTABLE RESOLUTION TESTS
# ########################


def test_executable_resolution_using_local_venv():
    with (
        ProxyRunner.test() as runner,
        isolated_example_project_foo_bar(runner),
    ):
        project_context = DgContext.for_project_environment(Path.cwd(), {})

        # Create a venv in the workspace root
        with pushd(project_context.workspace_root_path):
            subprocess.check_output(["uv", "venv"])

        assert project_context.is_project
        assert project_context.root_path == Path.cwd()
        assert project_context.has_venv
        assert project_context.venv_path == project_context.root_path / ".venv"

        # Resolve with the local venv
        assert str(project_context.get_executable("python")).startswith(
            str(project_context.venv_path)
        )

        # When venv is present at workspace root, use it
        workspace_context = DgContext.for_workspace_environment(
            project_context.workspace_root_path, {}
        )
        assert workspace_context.is_workspace
        assert workspace_context.has_venv
        assert workspace_context.venv_path == workspace_context.root_path / ".venv"
        assert str(workspace_context.get_executable("python")).startswith(
            str(workspace_context.venv_path)
        )

        # Go outside the workspace root. Now we should not be able to resolve anything because no
        # venv.
        general_context = DgContext.from_file_discovery_and_command_line_config(
            workspace_context.root_path.parent, {}
        )
        assert not general_context.has_venv
        with pytest.raises(DgError, match="Cannot resolve executable `python`"):
            general_context.get_executable("python")


def test_executable_resolution_using_ambient_environment():
    with (
        ProxyRunner.test() as runner,
        isolated_example_project_foo_bar(runner),
    ):
        project_context = DgContext.for_project_environment(Path.cwd(), {"use_local_venv": False})

        # Pop up to the workspace level, make sure we resolve to the same env
        with pushd(project_context.workspace_root_path):
            # Create a venv in the workspace root that we will NOT resolve to
            subprocess.check_output(["uv", "venv"])

        assert project_context.is_project
        assert project_context.root_path == Path.cwd()
        assert project_context.has_venv

        # Don't resolve using the local venv, either in the project or in the workspace root
        assert not str(project_context.get_executable("python")).startswith(
            str(project_context.workspace_root_path)
        )

        workspace_context = DgContext.for_workspace_environment(
            project_context.workspace_root_path, {"use_local_venv": False}
        )
        assert workspace_context.is_workspace
        assert workspace_context.has_venv
        assert not str(workspace_context.get_executable("python")).startswith(
            str(workspace_context.root_path)
        )

        # Go outside the workspace root and make sure we can still resolve executables
        general_context = DgContext.from_file_discovery_and_command_line_config(
            workspace_context.root_path.parent, {"use_local_venv": False}
        )
        assert not general_context.has_venv
        assert general_context.get_executable("python")


# ########################
# ##### CONFIG TESTS
# ########################

# Combine the many cases inside each test function for each speed, we don't want to set up
# isolated projects etc for every case.


def test_invalid_config_type():
    with ProxyRunner.test() as runner, isolated_example_workspace(runner):
        with _reset_pyproject_toml():
            _set_and_detect_missing_required_key(
                ("tool.dg.directory_type"), DgFileConfigDirectoryType
            )
        with _reset_pyproject_toml():
            _set_and_detect_mistyped_value(("tool.dg.directory_type"), DgFileConfigDirectoryType, 1)


def test_invalid_config_workspace():
    with ProxyRunner.test() as runner, isolated_example_workspace(runner, project_name="foo-bar"):
        cases = [
            "tool.dg.invalid_key",
            "tool.dg.project",
            "tool.dg.cli.invalid_key",
            "tool.dg.workspace.invalid_key",
            "tool.dg.workspace.projects[0].invalid_key",
            "tool.dg.workspace.scaffold_project_options.invalid_key",
        ]
        for path in cases:
            with _reset_pyproject_toml():
                _set_and_detect_invalid_key(path)

        cases = [
            ["tool.dg.cli.disable_cache", bool, 1],
            ["tool.dg.cli.cache_dir", str, 1],
            ["tool.dg.cli.verbose", bool, 1],
            ["tool.dg.cli.use_dg_managed_environment", bool, 1],
            ["tool.dg.cli.use_component_modules", Sequence[str], 1],
            ["tool.dg.cli.use_local_venv", bool, 1],
            ["tool.dg.workspace.projects", list, 1],
            ["tool.dg.workspace.projects[1]", dict, 1],
            ["tool.dg.workspace.projects[0].path", str, 1],
            ["tool.dg.workspace.scaffold_project_options", dict, 1],
            [
                "tool.dg.workspace.scaffold_project_options.use_editable_dagster",
                Union[bool, str],
                1,
            ],
            [
                "tool.dg.workspace.scaffold_project_options.use_editable_components_package_only",
                Union[bool, str],
                1,
            ],
        ]
        for path, expected_type, val in cases:
            with _reset_pyproject_toml():
                _set_and_detect_mistyped_value(path, expected_type, val)

        cases = [
            ["tool.dg.workspace.projects[0].path", str],
        ]
        for path, expected_type in cases:
            with _reset_pyproject_toml():
                _set_and_detect_missing_required_key(path, expected_type)


def test_invalid_config_project():
    with ProxyRunner.test() as runner, isolated_example_project_foo_bar(runner):
        paths = [
            "tool.dg.invalid_key",
            "tool.dg.project.invalid_key",
            "tool.dg.cli.invalid_key",
        ]
        for case in paths:
            with _reset_pyproject_toml():
                _set_and_detect_invalid_key(case)

        cases = [
            [("tool.dg.cli.verbose"), bool, 1],
            [("tool.dg.project.root_module"), str, 1],
            [("tool.dg.project.defs_module"), str, 1],
            [("tool.dg.project.code_location_name"), str, 1],
            [("tool.dg.project.code_location_target_module"), str, 1],
        ]
        for path, expected_type, val in cases:
            with _reset_pyproject_toml():
                _set_and_detect_mistyped_value(path, expected_type, val)

        cases = [
            ["tool.dg.project.root_module", str],
        ]
        for path, expected_type in cases:
            with _reset_pyproject_toml():
                _set_and_detect_missing_required_key(path, expected_type)


def test_code_location_config():
    with ProxyRunner.test() as runner, isolated_example_project_foo_bar(runner):
        context = DgContext.for_project_environment(Path.cwd(), {})
        assert context.code_location_target_module_name == "foo_bar.definitions"
        assert context.code_location_name == "foo-bar"

        with modify_toml_as_dict(Path("pyproject.toml")) as toml:
            create_toml_node(
                toml,
                ("tool", "dg", "project", "code_location_target_module"),
                "foo_bar._definitions",
            )
            create_toml_node(
                toml, ("tool", "dg", "project", "code_location_name"), "my-code_location"
            )

        context = DgContext.for_project_environment(Path.cwd(), {})
        assert context.code_location_target_module_name == "foo_bar._definitions"
        assert context.code_location_name == "my-code_location"


# ########################
# ##### HELPERS
# ########################


@contextmanager
def _reset_pyproject_toml():
    original = Path("pyproject.toml").read_text()
    yield
    Path("pyproject.toml").write_text(original)


def _set_and_detect_error(path: TomlPath, config_value: object, error_message: str):
    with modify_toml_as_dict(Path("pyproject.toml")) as toml:
        create_toml_node(toml, path, config_value)
    with pytest.raises(DgError, match=re.escape(error_message)):
        DgContext.from_file_discovery_and_command_line_config(Path.cwd(), {})


def _set_and_detect_invalid_key(str_path: str, config_value: object = True):
    path = toml_path_from_str(str_path)
    leading_str_path, key = toml_path_to_str(path[:-1]), path[-1]
    error_message = rf"Unrecognized fields in `{leading_str_path}`: ['{key}']"
    _set_and_detect_error(path, config_value, error_message)


# expected_type Any to handle typing constructs (`Literal` etc)
def _set_and_detect_mistyped_value(str_path: str, expected_type: Any, config_value: object):
    path = toml_path_from_str(str_path)
    expected_str = get_type_str(expected_type)
    error_message = (
        rf"Invalid value for `{str_path}`. Expected {expected_str}, got `{config_value}`"
    )
    _set_and_detect_error(path, config_value, error_message)


# expected_type Any to handle typing constructs (`Literal` etc)
def _set_and_detect_missing_required_key(str_path: str, expected_type: Any):
    path = toml_path_from_str(str_path)
    expected_str = get_type_str(expected_type)
    error_message = rf"Missing required value for `{str_path}`. Expected {expected_str}"
    with modify_toml_as_dict(Path("pyproject.toml")) as toml:
        delete_toml_node(toml, path)
    with pytest.raises(DgError, match=re.escape(error_message)):
        DgContext.from_file_discovery_and_command_line_config(Path.cwd(), {})
