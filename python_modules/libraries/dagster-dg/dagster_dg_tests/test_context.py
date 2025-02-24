from pathlib import Path

import pytest
from dagster_dg.context import DgContext
from dagster_dg.error import DgError
from dagster_dg.utils import pushd, set_toml_value

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

        # Test config properly set
        with modify_pyproject_toml() as pyproject_toml:
            set_toml_value(pyproject_toml, ("tool", "dg", "verbose"), True)
        context = DgContext.for_workspace_environment(path_arg, {})
        assert context.config.verbose is True


def test_context_in_project_in_workspace():
    with ProxyRunner.test() as runner, isolated_example_workspace(runner, project_name="foo"):
        project_path = Path.cwd() / "projects" / "foo"
        # go into a project subdirectory to make sure root resolution works
        path_arg = project_path / "foo_tests"

        context = DgContext.for_project_environment(path_arg, {})
        assert context.root_path == project_path
        assert context.config.verbose is False  # default

        # Test config inheritance from workspace
        with modify_pyproject_toml() as pyproject_toml:
            set_toml_value(pyproject_toml, ("tool", "dg", "verbose"), True)
        context = DgContext.for_project_environment(path_arg, {})
        assert context.config.verbose is True

        # Test config from project overrides workspace
        with pushd(project_path), modify_pyproject_toml() as pyproject_toml:
            set_toml_value(pyproject_toml, ("tool", "dg", "verbose"), False)
        context = DgContext.for_project_environment(path_arg, {})
        assert context.config.verbose is False


def test_context_in_project_outside_workspace():
    with ProxyRunner.test() as runner, isolated_example_project_foo_bar(runner):
        project_path = Path.cwd()
        # go into a project subdirectory to make sure root resolution works
        path_arg = project_path / "foo_tests"

        context = DgContext.for_project_environment(path_arg, {})
        assert context.root_path == project_path
        assert context.config.verbose is False

        with modify_pyproject_toml() as pyproject_toml:
            set_toml_value(pyproject_toml, ("tool", "dg", "verbose"), True)
        context = DgContext.for_project_environment(path_arg, {})
        assert context.config.verbose is True


def test_context_outside_project_or_workspace():
    with ProxyRunner.test() as runner, isolated_components_venv(runner):
        context = DgContext.from_config_file_discovery_and_cli_config(Path.cwd(), {})
        assert context.root_path == Path.cwd()
        assert context.config.verbose is False


def test_invalid_key_in_config():
    with ProxyRunner.test() as runner, isolated_example_workspace(runner):
        with modify_pyproject_toml() as pyproject_toml:
            set_toml_value(pyproject_toml, ("tool", "dg", "invalid_key"), True)
        with pytest.raises(
            DgError, match=r"Unrecognized fields in configuration: \['invalid_key'\]"
        ):
            DgContext.from_config_file_discovery_and_cli_config(Path.cwd(), {})
