import subprocess
from pathlib import Path

import pytest
from dagster_dg.utils import ensure_dagster_dg_tests_import, get_venv_executable, resolve_local_venv

ensure_dagster_dg_tests_import()

from dagster_dg_tests.utils import (
    ProxyRunner,
    assert_runner_result,
    crawl_cli_commands,
    isolated_components_venv,
)

# The tests in this file are designed to check error messages for basic precondition checks for
# command execution across all CLI commands. Many commands require execution with
# `dagster-components` available in some environment. Other commands additionally require execution
# in the context of a project, workspace, or component library package. As a rule, checks for
# these preconditions should run before any command logic. These tests ensure such checks are done.
#
# There is a test (`test_all_commands_represented_in_env_check_tests`) to ensure that all commands
# are represented in this file. Therefore when a new command is added to the CLI, it should be
# added to the appropriate list below. That will automatically make sure the appropriate precondition
# error messages are checked.


class CommandSpec:
    def __init__(self, command: tuple[str, ...], *args: str):
        self.command = command
        self.args = args

    def to_cli_args(self) -> tuple[str, ...]:
        return (*self.command, *self.args)


DEFAULT_COMPONENT_TYPE = "dagster_test.components.SimpleAssetComponent"

NO_REQUIRED_CONTEXT_COMMANDS = [
    CommandSpec(("scaffold",), "project"),
    CommandSpec(("scaffold", "project"), "foo"),
    CommandSpec(("scaffold", "workspace"), "foo"),
    CommandSpec(("scaffold", "dagster.asset"), "foo"),
    CommandSpec(("scaffold", "dagster.asset_check"), "foo"),
    CommandSpec(("scaffold", "dagster.schedule"), "foo"),
    CommandSpec(("scaffold", "dagster.sensor"), "foo"),
    CommandSpec(("plus", "login")),
]


COMPONENT_LIBRARY_CONTEXT_COMMANDS = [
    CommandSpec(("scaffold", "component-type"), "foo"),
]

REGISTRY_CONTEXT_COMMANDS = [
    CommandSpec(tuple(), "--rebuild-plugin-cache"),
    CommandSpec(("docs", "serve")),
    CommandSpec(("list", "component")),
    CommandSpec(("list", "plugins")),
    CommandSpec(("utils", "inspect-component-type"), DEFAULT_COMPONENT_TYPE),
]


PROJECT_CONTEXT_COMMANDS = [
    CommandSpec(("launch",), "--assets", "foo"),
    CommandSpec(("utils", "configure-editor"), "vscode"),
    CommandSpec(("utils", "generate-component-schema")),
    CommandSpec(("check", "yaml")),
    CommandSpec(("list", "defs")),
    CommandSpec(("list", "env")),
    CommandSpec(("scaffold", DEFAULT_COMPONENT_TYPE, "foot")),
]

WORKSPACE_CONTEXT_COMMANDS = [
    CommandSpec(("list", "project")),
]

WORKSPACE_OR_PROJECT_CONTEXT_COMMANDS = [
    CommandSpec(("dev",)),
    CommandSpec(("check", "defs")),
]

# ########################
# ##### TESTS
# ########################


@pytest.mark.skip("temp")
def test_all_commands_represented_in_env_check_tests() -> None:
    commands = crawl_cli_commands()

    all_listed_commands = [
        spec.command
        for spec in [
            *NO_REQUIRED_CONTEXT_COMMANDS,
            *COMPONENT_LIBRARY_CONTEXT_COMMANDS,
            *PROJECT_CONTEXT_COMMANDS,
            *WORKSPACE_CONTEXT_COMMANDS,
            *WORKSPACE_OR_PROJECT_CONTEXT_COMMANDS,
            *REGISTRY_CONTEXT_COMMANDS,
        ]
    ]
    crawled_commands = [tuple(key[1:]) for key in commands.keys() if len(key) > 1]
    unlisted_commands = set(crawled_commands) - set(all_listed_commands)
    assert not unlisted_commands, f"Unlisted commands have no env tests: {unlisted_commands}"


@pytest.mark.parametrize(
    "spec",
    [
        *PROJECT_CONTEXT_COMMANDS,
    ],
    ids=lambda spec: "-".join(spec.command),
)
def test_no_local_venv_failure(spec: CommandSpec) -> None:
    if spec.command == ("docs", "serve"):
        pytest.skip("docs serve command hangs on this test")
    with ProxyRunner.test() as runner, runner.isolated_filesystem():
        result = runner.invoke(*spec.to_cli_args())
        assert_runner_result(result, exit_0=False)


@pytest.mark.parametrize(
    "spec",
    [
        *PROJECT_CONTEXT_COMMANDS,
    ],
    ids=lambda spec: "-".join(spec.command),
)
def test_no_local_dagster_components_failure(spec: CommandSpec) -> None:
    with (
        ProxyRunner.test(use_fixed_test_components=True) as runner,
        isolated_components_venv(runner),
    ):
        _uninstall_dagster_from_local_venv(Path.cwd())
        result = runner.invoke(*spec.to_cli_args())
        assert_runner_result(result, exit_0=False)


@pytest.mark.parametrize(
    "spec",
    [
        # *COMPONENT_LIBRARY_CONTEXT_COMMANDS,
        *REGISTRY_CONTEXT_COMMANDS,
        # *PROJECT_CONTEXT_COMMANDS,
    ],
    ids=lambda spec: "-".join(spec.command),
)
def test_no_ambient_dagster_components_failure(spec: CommandSpec) -> None:
    with ProxyRunner.test(use_fixed_test_components=True) as runner, runner.isolated_filesystem():
        cli_args = _add_global_cli_options(spec.to_cli_args())
        # Set $PATH to /dev/null to ensure that the `dagster-components` executable is not found
        result = runner.invoke(*cli_args, env={"PATH": "/dev/null"})
        assert_runner_result(result, exit_0=False)
        assert "Could not resolve the `dagster-components` executable" in result.output


@pytest.mark.parametrize("spec", PROJECT_CONTEXT_COMMANDS, ids=lambda spec: "-".join(spec.command))
def test_no_project_failure(spec: CommandSpec) -> None:
    with (
        ProxyRunner.test(use_fixed_test_components=True) as runner,
        isolated_components_venv(runner),
    ):
        result = runner.invoke(*spec.to_cli_args())
        assert_runner_result(result, exit_0=False)
        assert "must be run inside a Dagster project directory" in result.output

        runner.invoke("scaffold", "project", "foo")
        result = runner.invoke(*spec.to_cli_args())
        assert_runner_result(result, exit_0=False)
        assert "must be run inside a Dagster project directory" in result.output
        assert "You may have wanted to" in result.output
        assert "/foo" in result.output


@pytest.mark.parametrize(
    "spec", COMPONENT_LIBRARY_CONTEXT_COMMANDS, ids=lambda spec: "-".join(spec.command)
)
def test_no_component_library_failure(spec: CommandSpec) -> None:
    with (
        ProxyRunner.test(use_fixed_test_components=True) as runner,
        isolated_components_venv(runner),
    ):
        result = runner.invoke(*spec.to_cli_args())
        assert_runner_result(result, exit_0=False)
        assert "must be run inside a Dagster component library directory" in result.output


@pytest.mark.parametrize(
    "spec", WORKSPACE_CONTEXT_COMMANDS, ids=lambda spec: "-".join(spec.command)
)
def test_no_workspace_failure(spec: CommandSpec) -> None:
    with (
        ProxyRunner.test(use_fixed_test_components=True) as runner,
        isolated_components_venv(runner),
    ):
        result = runner.invoke(*spec.to_cli_args())
        assert_runner_result(result, exit_0=False)
        assert "must be run inside a Dagster workspace directory" in result.output
        assert "You may have wanted to" not in result.output

        runner.invoke("scaffold", "workspace", "foo")
        result = runner.invoke(*spec.to_cli_args())
        assert_runner_result(result, exit_0=False)
        assert "must be run inside a Dagster workspace directory" in result.output
        assert "You may have wanted to" in result.output
        assert "/foo" in result.output


@pytest.mark.parametrize(
    "spec", WORKSPACE_OR_PROJECT_CONTEXT_COMMANDS, ids=lambda spec: "-".join(spec.command)
)
def test_no_workspace_or_project_failure(spec: CommandSpec) -> None:
    with (
        ProxyRunner.test(use_fixed_test_components=True) as runner,
        isolated_components_venv(runner),
    ):
        result = runner.invoke(*spec.to_cli_args())
        assert_runner_result(result, exit_0=False)
        assert "must be run inside a Dagster workspace or project directory" in result.output
        assert "You may have wanted to" not in result.output

        runner.invoke("scaffold", "project", "foo")
        result = runner.invoke(*spec.to_cli_args())
        assert_runner_result(result, exit_0=False)
        assert "must be run inside a Dagster workspace or project directory" in result.output
        assert "You may have wanted to" in result.output
        assert "/foo" in result.output


# ########################
# ##### HELPERS
# ########################


# `dg scaffold` is special because global options have to be inserted before the
# subcommand name, instead of just at the end.
def _add_global_cli_options(cli_args: tuple[str, ...], *global_opts: str) -> list[str]:
    if cli_args[0] == "scaffold":
        return [cli_args[0], *global_opts, *cli_args[1:]]
    else:
        return [*cli_args, *global_opts]


def _uninstall_dagster_from_local_venv(path: Path) -> None:
    local_venv = resolve_local_venv(Path.cwd())
    assert local_venv, f"No local venv resolvable from {path}"
    subprocess.check_output(
        [
            "uv",
            "pip",
            "uninstall",
            "--python",
            str(get_venv_executable(local_venv)),
            "dagster",
        ],
    )
