from contextlib import contextmanager
from pathlib import Path
from typing import Union, get_args

import pytest
from dagster_dg.config import DgFileConfigDirectoryType
from dagster_dg.context import DgContext
from dagster_dg.error import DgError
from dagster_dg.utils import delete_toml_value, pushd, set_toml_value

from dagster_dg_tests.utils import (
    ProxyRunner,
    isolated_components_venv,
    isolated_example_project_foo_bar,
    isolated_example_workspace,
    modify_pyproject_toml,
)


def test_context_in_workspace():
    with ProxyRunner.test() as runner, isolated_example_workspace(runner):
        # go into a subdirectory to make sure root resolution works
        path_arg = Path.cwd() / "libraries"

        context = DgContext.for_workspace_environment(path_arg, {})
        assert context.root_path == Path.cwd()
        assert context.workspace_root_path == Path.cwd()

        # Test config properly set
        with modify_pyproject_toml() as pyproject_toml:
            set_toml_value(pyproject_toml, ("tool", "dg", "cli", "verbose"), True)
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
        with modify_pyproject_toml() as pyproject_toml:
            set_toml_value(pyproject_toml, ("tool", "dg", "cli", "verbose"), True)
        context = DgContext.for_project_environment(path_arg, {})
        assert context.config.cli.verbose is True

        # Test config from project overrides workspace
        with pushd(project_path), modify_pyproject_toml() as pyproject_toml:
            set_toml_value(pyproject_toml, ("tool", "dg", "cli", "verbose"), False)
        context = DgContext.for_project_environment(path_arg, {})
        assert context.config.cli.verbose is False


def test_context_in_project_outside_workspace():
    with ProxyRunner.test() as runner, isolated_example_project_foo_bar(runner, in_workspace=False):
        project_path = Path.cwd()
        # go into a project subdirectory to make sure root resolution works
        path_arg = project_path / "foo_tests"

        context = DgContext.for_project_environment(path_arg, {})
        assert context.root_path == project_path
        assert context.workspace_root_path is None
        assert context.config.cli.verbose is False

        with modify_pyproject_toml() as pyproject_toml:
            set_toml_value(pyproject_toml, ("tool", "dg", "cli", "verbose"), True)
        context = DgContext.for_project_environment(path_arg, {})
        assert context.config.cli.verbose is True


def test_context_outside_project_or_workspace():
    with ProxyRunner.test() as runner, isolated_components_venv(runner):
        context = DgContext.from_file_discovery_and_command_line_config(Path.cwd(), {})
        assert context.root_path == Path.cwd()
        assert context.workspace_root_path is None
        assert context.config.cli.verbose is False


# ########################
# ##### CONFIG TESTS
# ########################

# Combine the many cases inside each test function for each speed, we don't want to set up
# isolated projects etc for every case.


def test_invalid_config_type():
    with ProxyRunner.test() as runner, isolated_example_workspace(runner):
        with _reset_pyproject_toml():
            _set_and_detect_missing_required_key(
                ("tool", "dg", "directory_type"), get_args(DgFileConfigDirectoryType)
            )
        with _reset_pyproject_toml():
            _set_and_detect_mistyped_value(
                ("tool", "dg", "directory_type"), get_args(DgFileConfigDirectoryType), 1
            )


def test_invalid_config_workspace():
    with ProxyRunner.test() as runner, isolated_example_workspace(runner, "foo-bar"):
        paths = [
            ("tool", "dg", "invalid_key"),
            ("tool", "dg", "project"),
            ("tool", "dg", "library"),
            ("tool", "dg", "cli", "invalid_key"),
        ]
        for case in paths:
            with _reset_pyproject_toml():
                _set_and_detect_invalid_key(case)

        cases = [
            [("tool", "dg", "cli", "disable_cache"), bool, 1],
            [("tool", "dg", "cli", "cache_dir"), str, 1],
            [("tool", "dg", "cli", "verbose"), bool, 1],
            [("tool", "dg", "cli", "builtin_component_lib"), str, 1],
            [("tool", "dg", "cli", "use_dg_managed_environment"), bool, 1],
            [("tool", "dg", "cli", "require_local_venv"), bool, 1],
        ]
        for path, expected_type, val in cases:
            with _reset_pyproject_toml():
                _set_and_detect_mistyped_value(path, expected_type, val)


def test_invalid_config_project():
    with ProxyRunner.test() as runner, isolated_example_project_foo_bar(runner):
        paths = [
            ("tool", "dg", "invalid_key"),
            ("tool", "dg", "project", "invalid_key"),
            ("tool", "dg", "library"),
            ("tool", "dg", "cli", "invalid_key"),
        ]
        for case in paths:
            with _reset_pyproject_toml():
                _set_and_detect_invalid_key(case)

        cases = [
            [("tool", "dg", "cli", "verbose"), bool, 1],
            [("tool", "dg", "project", "root_module"), str, 1],
            [("tool", "dg", "project", "components_module"), str, 1],
        ]
        for path, expected_type, val in cases:
            with _reset_pyproject_toml():
                _set_and_detect_mistyped_value(path, expected_type, val)

        cases = [
            [("tool", "dg", "project", "root_module"), str],
        ]
        for path, expected_type in cases:
            with _reset_pyproject_toml():
                _set_and_detect_missing_required_key(path, expected_type)


# ########################
# ##### HELPERS
# ########################


@contextmanager
def _reset_pyproject_toml():
    original = Path("pyproject.toml").read_text()
    yield
    Path("pyproject.toml").write_text(original)


def _set_and_detect_error(path: tuple[str, ...], config_value: object, error_message: str):
    with modify_pyproject_toml() as toml:
        set_toml_value(toml, path, config_value)
    with pytest.raises(DgError, match=error_message):
        DgContext.from_file_discovery_and_command_line_config(Path.cwd(), {})


def _set_and_detect_invalid_key(path: tuple[str, ...], config_value: object = True):
    leading_path, key = ".".join(path[:-1]), path[-1]
    error_message = rf"Unrecognized fields in `{leading_path}`: \['{key}'\]"
    _set_and_detect_error(path, config_value, error_message)


# Accept tuple[str, ...] for literals
def _set_and_detect_mistyped_value(
    path: tuple[str, ...], expected_type: Union[type, tuple[str, ...]], config_value: object
):
    key = ".".join(path)
    expected_str = _get_expected_type_str(expected_type)
    error_message = rf"Invalid value for `{key}`. Expected {expected_str}, got `{config_value}`"
    _set_and_detect_error(path, config_value, error_message)


def _set_and_detect_missing_required_key(
    path: tuple[str, ...], expected_type: Union[type, tuple[str, ...]]
):
    key = ".".join(path)
    expected_str = _get_expected_type_str(expected_type)
    error_message = rf"Missing required value for `{key}`. Expected {expected_str}"
    with modify_pyproject_toml() as toml:
        delete_toml_value(toml, path)
    with pytest.raises(DgError, match=error_message):
        DgContext.from_file_discovery_and_command_line_config(Path.cwd(), {})


def _get_expected_type_str(expected_type: Union[type, tuple[str, ...]]) -> str:
    return (
        expected_type.__name__
        if isinstance(expected_type, type)
        else " or ".join([f'"{t}"' for t in expected_type])
    )
