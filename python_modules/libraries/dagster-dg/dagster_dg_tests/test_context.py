import re
import tempfile
import textwrap
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
    get_toml_node,
    is_windows,
    modify_toml_as_dict,
    pushd,
    set_toml_node,
    toml_path_from_str,
    toml_path_to_str,
)
from dagster_dg.utils.warnings import DgWarningIdentifier
from dagster_shared.utils.config import get_default_dg_user_config_path

from dagster_dg_tests.utils import (
    ConfigFileType,
    ProxyRunner,
    assert_runner_result,
    dg_does_not_warn,
    dg_warns,
    isolated_components_venv,
    isolated_example_project_foo_bar,
    isolated_example_workspace,
    modify_dg_toml_config_as_dict,
)

# These tests also handle making sure config is properly read and config inheritance


@pytest.mark.parametrize("config_file", ["dg.toml", "pyproject.toml"])
def test_context_in_workspace(config_file: ConfigFileType):
    with (
        ProxyRunner.test() as runner,
        isolated_example_workspace(runner, workspace_config_file_type=config_file),
    ):
        # go into a subdirectory to make sure root resolution works
        path_arg = Path.cwd() / "projects"

        context = DgContext.for_workspace_environment(path_arg, {})
        assert context.root_path == Path.cwd()
        assert context.workspace_root_path == Path.cwd()

        # Test config properly set
        with modify_dg_toml_config_as_dict(Path(config_file)) as toml_dict:
            create_toml_node(toml_dict, ("cli", "verbose"), True)
        context = DgContext.for_workspace_environment(path_arg, {})
        assert context.config.cli.verbose is True


@pytest.mark.parametrize("project_config_file", ["dg.toml", "pyproject.toml"])
@pytest.mark.parametrize("workspace_config_file", ["dg.toml", "pyproject.toml"])
def test_context_in_project_in_workspace(
    project_config_file: ConfigFileType, workspace_config_file: ConfigFileType
):
    with (
        ProxyRunner.test() as runner,
        isolated_example_workspace(
            runner,
            project_name="foo-bar",
            workspace_config_file_type=workspace_config_file,
            project_config_file_type=project_config_file,
        ),
    ):
        project_path = Path.cwd() / "projects" / "foo-bar"
        # go into a project subdirectory to make sure root resolution works
        path_arg = project_path / "foo_bar_tests"

        context = DgContext.for_project_environment(path_arg, {})
        assert context.root_path == project_path
        assert context.workspace_root_path == Path.cwd()
        assert context.config.cli.verbose is False  # default

        # Test config inheritance from workspace
        with modify_dg_toml_config_as_dict(Path(workspace_config_file)) as toml_dict:
            create_toml_node(toml_dict, ("cli", "verbose"), True)
        context = DgContext.for_project_environment(path_arg, {})
        assert context.config.cli.verbose is True

        # Test cli config in project is ignored and generates warning
        with (
            pushd(project_path),
            modify_dg_toml_config_as_dict(Path(project_config_file)) as project_toml,
        ):
            create_toml_node(project_toml, ("cli", "verbose"), False)
        with dg_warns(match="cli` section detected in workspace project"):
            context = DgContext.for_project_environment(path_arg, {})
        assert context.config.cli.verbose is True


@pytest.mark.parametrize("config_file", ["dg.toml", "pyproject.toml"])
def test_context_in_project_outside_workspace(config_file: ConfigFileType):
    with (
        ProxyRunner.test() as runner,
        isolated_example_project_foo_bar(runner, in_workspace=False, config_file_type=config_file),
    ):
        project_path = Path.cwd()
        # go into a project subdirectory to make sure root resolution works
        path_arg = project_path / "foo_tests"

        context = DgContext.for_project_environment(path_arg, {})
        assert context.root_path == project_path
        assert context.is_workspace is False
        assert context.config.cli.verbose is False

        # Test CLI setting is used in project outside of workspace
        with modify_dg_toml_config_as_dict(Path(config_file)) as toml:
            create_toml_node(toml, ("cli", "verbose"), True)
        context = DgContext.for_project_environment(path_arg, {})
        assert context.config.cli.verbose is True


def test_context_outside_project_or_workspace():
    with ProxyRunner.test() as runner, isolated_components_venv(runner):
        context = DgContext.from_file_discovery_and_command_line_config(Path.cwd(), {})
        assert context.root_path == Path.cwd()
        assert context.is_workspace is False
        assert context.config.cli.verbose is False


@pytest.mark.parametrize("user_config_file", ["default", "xdg_config_home", "explicit_env_var"])
def test_context_with_user_config(monkeypatch, user_config_file: str):
    if user_config_file == "xdg_config_home" and is_windows():
        pytest.skip("XDG_CONFIG_HOME is not supported on Windows")

    with (
        ProxyRunner.test() as runner,
        isolated_components_venv(runner),
        tempfile.TemporaryDirectory() as temp_dir,
    ):
        sample_config = textwrap.dedent("""
            [cli]
            verbose = true
        """)
        if user_config_file == "default":
            monkeypatch.setenv("HOME", str(temp_dir))
            config_path = get_default_dg_user_config_path()  # this will use the patched HOME
            config_path.parent.mkdir(parents=True, exist_ok=True)
        elif user_config_file == "xdg_config_home":
            monkeypatch.setenv("XDG_CONFIG_HOME", str(temp_dir))
            config_path = Path(temp_dir) / "dg.toml"
        else:  # env_var
            config_path = Path(temp_dir) / "somefile.toml"
            monkeypatch.setenv("DG_CLI_CONFIG", str(config_path))
        config_path.write_text(sample_config)

        context = DgContext.from_file_discovery_and_command_line_config(Path.cwd(), {})
        assert context.root_path == Path.cwd()
        assert context.config.cli.verbose is True


# Temporary test until we switch src layout to the default.
def test_context_with_root_layout():
    with (
        ProxyRunner.test() as runner,
        isolated_example_project_foo_bar(runner, in_workspace=False, package_layout="root"),
    ):
        context = DgContext.from_file_discovery_and_command_line_config(Path.cwd(), {})
        assert context.root_path == Path.cwd()
        assert context.defs_path == Path.cwd() / "foo_bar" / "defs"

        result = runner.invoke("list", "defs")
        assert_runner_result(result)


def test_warning_suppression():
    with (
        ProxyRunner.test() as runner,
        isolated_example_workspace(
            runner,
            project_name="foo-bar",
        ),
    ):
        with modify_dg_toml_config_as_dict(Path("dg.toml")) as toml:
            create_toml_node(
                toml, ("cli", "suppress_warnings"), ["cli_config_in_workspace_project"]
            )
        with modify_dg_toml_config_as_dict(Path("projects/foo-bar/pyproject.toml")) as toml:
            create_toml_node(toml, ("cli", "verbose"), True)

        with dg_does_not_warn(match="cli` section detected in workspace project"):
            DgContext.for_project_environment(Path("projects/foo-bar"), {})


def test_setup_cfg_entry_point():
    with (
        ProxyRunner.test() as runner,
        isolated_example_project_foo_bar(runner, in_workspace=False),
    ):
        # Delete the entry point section from pyproject.toml
        with modify_toml_as_dict(Path("pyproject.toml")) as toml:
            delete_toml_node(toml, ("project", "entry-points", "dagster_dg.plugin"))
        # Create a setup.cfg file with the entry point
        with open("setup.cfg", "w") as f:
            f.write(
                """
                [options.entry_points]
                dagster_dg.plugin =
                    foo_bar = foo_bar.lib
                """
            )
        context = DgContext.for_project_environment(Path.cwd(), {})
        assert context.is_plugin


def test_deprecated_entry_point_group_warning():
    with (
        ProxyRunner.test() as runner,
        isolated_example_project_foo_bar(runner),
    ):
        with modify_toml_as_dict(Path("pyproject.toml")) as toml_dict:
            plugin_entry_points = get_toml_node(
                toml_dict, ("project", "entry-points", "dagster_dg.plugin"), dict
            )
            set_toml_node(
                toml_dict, ("project", "entry-points", "dagster_dg.library"), plugin_entry_points
            )
            delete_toml_node(toml_dict, ("project", "entry-points", "dagster_dg.plugin"))

        expected_match = "deprecated `dagster_dg.library` entry point group"
        with dg_warns(expected_match):
            DgContext.for_project_environment(Path("foo-bar"), {})
        with dg_warns(expected_match):
            DgContext.for_workspace_or_project_environment(Path("foo-bar"), {})
        with dg_warns(expected_match):
            DgContext.for_component_library_environment(Path("foo-bar"), {})


@pytest.mark.skipif(is_windows(), reason="~/.dg.toml was never config location on windows")
def test_deprecated_dg_toml_location_warning(tmp_path, monkeypatch):
    home = tmp_path
    Path(home / ".dg.toml").touch()
    monkeypatch.setenv("HOME", str(home))
    with dg_warns(match="Found config file ~/.dg.toml"):
        DgContext.from_file_discovery_and_command_line_config(Path.cwd(), {})


# ########################
# ##### CONFIG TESTS
# ########################

# Combine the many cases inside each test function for each speed, we don't want to set up
# isolated projects etc for every case.
#
# These all use pyproject.toml instead of dg.toml but validation happens after loading which is
# tested above, so this applies to dg.toml also.


@pytest.mark.parametrize("config_file", ["dg.toml", "pyproject.toml"])
def test_invalid_config_type(config_file: ConfigFileType):
    with (
        ProxyRunner.test() as runner,
        isolated_example_workspace(runner, workspace_config_file_type=config_file),
    ):
        with _reset_config_file(config_file):
            _set_and_detect_missing_required_key(
                config_file, "directory_type", DgFileConfigDirectoryType
            )
        with _reset_config_file(config_file):
            _set_and_detect_mistyped_value(
                config_file, "directory_type", DgFileConfigDirectoryType, 1
            )


@pytest.mark.parametrize("config_file", ["dg.toml", "pyproject.toml"])
def test_invalid_config_workspace(config_file: ConfigFileType):
    with (
        ProxyRunner.test() as runner,
        isolated_example_workspace(
            runner, project_name="foo-bar", workspace_config_file_type=config_file
        ),
    ):
        cases = [
            "invalid_key",
            "project",
            "cli.invalid_key",
            "workspace.invalid_key",
            "workspace.projects[0].invalid_key",
            "workspace.scaffold_project_options.invalid_key",
        ]
        for path in cases:
            with _reset_config_file(config_file):
                _set_and_detect_invalid_key(config_file, path)

        cases = [
            ["cli.disable_cache", bool, 1],
            ["cli.cache_dir", str, 1],
            ["cli.verbose", bool, 1],
            ["cli.use_component_modules", Sequence[str], 1],
            ["cli.suppress_warnings", list[DgWarningIdentifier], 1],
            ["workspace.projects", list, 1],
            ["workspace.projects[1]", dict, 1],
            ["workspace.projects[0].path", str, 1],
            ["workspace.scaffold_project_options", dict, 1],
            [
                "workspace.scaffold_project_options.use_editable_dagster",
                Union[bool, str],
                1,
            ],
        ]
        for path, expected_type, val in cases:
            with _reset_config_file(config_file):
                _set_and_detect_mistyped_value(config_file, path, expected_type, val)

        cases = [
            ["workspace.projects[0].path", str],
        ]
        for path, expected_type in cases:
            with _reset_config_file(config_file):
                _set_and_detect_missing_required_key(config_file, path, expected_type)


# @pytest.mark.parametrize("config_file", ["dg.toml", "pyproject.toml"])
@pytest.mark.parametrize("config_file", ["dg.toml"])
def test_invalid_config_project(config_file: ConfigFileType):
    with (
        ProxyRunner.test() as runner,
        isolated_example_project_foo_bar(runner, config_file_type=config_file),
    ):
        paths = [
            "invalid_key",
            "project.invalid_key",
            "project.python_environment.invalid_key",
            "cli.invalid_key",
        ]
        for case in paths:
            with _reset_config_file(config_file):
                _set_and_detect_invalid_key(config_file, case)

        cases = [
            ["cli.verbose", bool, 1],
            ["project.root_module", str, 1],
            ["project.defs_module", str, 1],
            ["project.code_location_name", str, 1],
            ["project.code_location_target_module", str, 1],
            ["project.python_environment", dict, 1],
            ["project.python_environment.path", str, 1],
            ["project.python_environment.active", bool, 1],
            ["project.python_environment.uv_managed", bool, 1],
        ]
        for path, expected_type, val in cases:
            with _reset_config_file(config_file):
                _set_and_detect_mistyped_value(config_file, path, expected_type, val)

        cases = [
            ["project.root_module", str],
        ]
        for path, expected_type in cases:
            with _reset_config_file(config_file):
                _set_and_detect_missing_required_key(config_file, path, expected_type)

        # Multiple conflicting settings
        with _reset_config_file(config_file):
            python_env_full_key = _get_full_str_path(config_file, "project.python_environment")
            with modify_dg_toml_config_as_dict(Path(config_file)) as toml:
                toml["project"]["python_environment"]["active"] = True
                toml["project"]["python_environment"]["uv_managed"] = True
            with pytest.raises(
                DgError, match=f"Found conflicting settings in `{python_env_full_key}`"
            ):
                DgContext.from_file_discovery_and_command_line_config(Path.cwd(), {})


@pytest.mark.parametrize("config_file", ["dg.toml", "pyproject.toml"])
def test_deprecated_config_project(config_file: ConfigFileType):
    with (
        ProxyRunner.test() as runner,
        isolated_example_project_foo_bar(runner, config_file_type=config_file),
    ):
        full_key = _get_full_str_path(config_file, "project.python_environment")
        for value in ["persistent_uv", "active"]:
            with _reset_config_file(config_file):
                with modify_dg_toml_config_as_dict(Path(config_file)) as toml:
                    create_toml_node(toml, ("project", "python_environment"), value)
                with dg_warns(match=f'`{full_key} = "{value}"` is deprecated'):
                    context = DgContext.from_file_discovery_and_command_line_config(Path.cwd(), {})
                if value == "persistent_uv":
                    assert context.config.project.python_environment.uv_managed is True  # type: ignore
                elif value == "active":
                    assert context.config.project.python_environment.active is True  # type: ignore


@pytest.mark.parametrize("config_file", ["dg.toml", "pyproject.toml"])
def test_code_location_config(config_file: ConfigFileType):
    with (
        ProxyRunner.test() as runner,
        isolated_example_project_foo_bar(runner, config_file_type=config_file),
    ):
        context = DgContext.for_project_environment(Path.cwd(), {})
        assert context.code_location_target_module_name == "foo_bar.definitions"
        assert context.code_location_name == "foo-bar"

        with modify_dg_toml_config_as_dict(Path(config_file)) as toml:
            create_toml_node(
                toml,
                ("project", "code_location_target_module"),
                "foo_bar._definitions",
            )
            create_toml_node(toml, ("project", "code_location_name"), "my-code_location")

        context = DgContext.for_project_environment(Path.cwd(), {})
        assert context.code_location_target_module_name == "foo_bar._definitions"
        assert context.code_location_name == "my-code_location"


def test_virtual_env_mismatch_warning():
    with (
        ProxyRunner.test() as runner,
        isolated_example_project_foo_bar(runner, in_workspace=False, python_environment="active"),
    ):
        with dg_warns(match="virtual environment does not match"):
            DgContext.for_project_environment(Path.cwd(), {})
        with dg_warns(match="virtual environment does not match"):
            DgContext.for_workspace_or_project_environment(Path.cwd(), {})


# ########################
# ##### HELPERS
# ########################


@contextmanager
def _reset_config_file(config_file: ConfigFileType):
    original = Path(config_file).read_text()
    yield
    Path(config_file).write_text(original)


def _get_full_str_path(config_file: ConfigFileType, str_path: str) -> str:
    if config_file == "pyproject.toml":
        return f"tool.dg.{str_path}" if str_path else "tool.dg"
    else:
        return str_path if str_path else "<root>"


def _set_and_detect_error(
    config_file: ConfigFileType, path: TomlPath, config_value: object, error_message: str
):
    with modify_dg_toml_config_as_dict(Path(config_file)) as toml:
        create_toml_node(toml, path, config_value)
    with pytest.raises(DgError, match=re.escape(error_message)):
        DgContext.from_file_discovery_and_command_line_config(Path.cwd(), {})


def _set_and_detect_invalid_key(
    config_file: ConfigFileType, str_path: str, config_value: object = True
):
    path = toml_path_from_str(str_path)
    leading_str_path, key = toml_path_to_str(path[:-1]), path[-1]
    full_leading_str_path = _get_full_str_path(config_file, leading_str_path)
    error_message = rf"Unrecognized fields at `{full_leading_str_path}`: ['{key}']"
    _set_and_detect_error(config_file, path, config_value, error_message)


# expected_type Any to handle typing constructs (`Literal` etc)
def _set_and_detect_mistyped_value(
    config_file: ConfigFileType, str_path: str, expected_type: Any, config_value: object
):
    path = toml_path_from_str(str_path)
    expected_str = get_type_str(expected_type)
    full_str_path = _get_full_str_path(config_file, str_path)
    error_message = (
        rf"Invalid value for `{full_str_path}`. Expected {expected_str}, got `{config_value}`"
    )
    _set_and_detect_error(config_file, path, config_value, error_message)


# expected_type Any to handle typing constructs (`Literal` etc)
def _set_and_detect_missing_required_key(
    config_file: ConfigFileType, str_path: str, expected_type: Any
):
    path = toml_path_from_str(str_path)
    expected_str = get_type_str(expected_type)
    full_str_path = _get_full_str_path(config_file, str_path)
    error_message = rf"Missing required value for `{full_str_path}`. Expected {expected_str}"
    with modify_dg_toml_config_as_dict(Path(config_file)) as toml:
        delete_toml_node(toml, path)
    with pytest.raises(DgError, match=re.escape(error_message)):
        DgContext.from_file_discovery_and_command_line_config(Path.cwd(), {})
