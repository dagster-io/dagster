import subprocess
from pathlib import Path

import click
import pytest
from dagster_dg.cli import cli
from dagster_dg.utils import get_venv_executable, resolve_local_venv
from dagster_dg_tests.utils import ProxyRunner, assert_runner_result, isolated_components_venv

# The tests in this file are designed to check error messages for basic precondition checks for
# command execution across all CLI commands. Many commands require execution with
# `dagster-components` available in some environment. Other commands additionally require execution
# in the context of a code location, deployment, or component library package. As a rule, checks for
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


DEFAULT_COMPONENT_TYPE = "simple_asset@dagster_components.test"

NO_REQUIRED_CONTEXT_COMMANDS = [
    CommandSpec(("code-location", "scaffold"), "foo"),
    CommandSpec(("deployment", "scaffold"), "foo"),
]

COMPONENT_LIBRARY_CONTEXT_COMMANDS = [
    CommandSpec(("component-type", "scaffold"), "foo"),
]

REGISTRY_CONTEXT_COMMANDS = [
    CommandSpec(tuple(), "--rebuild-component-registry"),
    CommandSpec(("component-type", "info"), DEFAULT_COMPONENT_TYPE),
    CommandSpec(("component-type", "docs"), DEFAULT_COMPONENT_TYPE),
    CommandSpec(("component-type", "list")),
]

CODE_LOCATION_CONTEXT_COMMANDS = [
    CommandSpec(("code-location", "configure-editor"), "vscode"),
    CommandSpec(("code-location", "generate-component-schema")),
    CommandSpec(("component", "check")),
    CommandSpec(("component", "list")),
    CommandSpec(("component", "scaffold"), DEFAULT_COMPONENT_TYPE, "foot"),
]

DEPLOYMENT_CONTEXT_COMMANDS = [
    CommandSpec(("code-location", "list")),
]

DEPLOYMENT_OR_CODE_LOCATION_CONTEXT_COMMANDS = [
    CommandSpec(("dev",)),
]

# ########################
# ##### TESTS
# ########################


def test_all_commands_represented_in_env_check_tests() -> None:
    commands: dict[tuple[str, ...], click.Command] = {}

    # Note that this does not pick up:
    # - all `component scaffold` subcommands, because these are dynamically generated and vary across
    #   environment. We still test one of these below though.
    # - special --ACTION options with callbacks (e.g. `--rebuild-component-registry`)
    def crawl(command: click.Command, path: tuple[str, ...]) -> None:
        assert command.name
        new_path = (*path, command.name)
        if isinstance(command, click.Group) and not new_path == ("dg", "component", "scaffold"):
            for subcommand in command.commands.values():
                assert subcommand.name
                crawl(subcommand, new_path)
        else:
            commands[new_path] = command

    crawl(cli, tuple())

    all_listed_commands = [
        spec.command
        for spec in [
            *NO_REQUIRED_CONTEXT_COMMANDS,
            *COMPONENT_LIBRARY_CONTEXT_COMMANDS,
            *CODE_LOCATION_CONTEXT_COMMANDS,
            *DEPLOYMENT_CONTEXT_COMMANDS,
            *DEPLOYMENT_OR_CODE_LOCATION_CONTEXT_COMMANDS,
            *REGISTRY_CONTEXT_COMMANDS,
        ]
    ]
    crawled_commands = [tuple(key[1:]) for key in commands.keys() if len(key) > 1]
    unlisted_commands = set(crawled_commands) - set(all_listed_commands)
    assert not unlisted_commands, f"Unlisted commands have no env tests: {unlisted_commands}"


@pytest.mark.parametrize(
    "spec",
    [
        *COMPONENT_LIBRARY_CONTEXT_COMMANDS,
        *REGISTRY_CONTEXT_COMMANDS,
        *CODE_LOCATION_CONTEXT_COMMANDS,
    ],
    ids=lambda spec: "-".join(spec.command),
)
def test_no_local_venv_failure(spec: CommandSpec) -> None:
    with ProxyRunner.test() as runner, runner.isolated_filesystem():
        result = runner.invoke(*spec.to_cli_args())
        assert_runner_result(result, exit_0=False)
        assert "no virtual environment (`.venv` dir) could be found" in result.output


@pytest.mark.parametrize(
    "spec",
    [
        *COMPONENT_LIBRARY_CONTEXT_COMMANDS,
        *REGISTRY_CONTEXT_COMMANDS,
        *CODE_LOCATION_CONTEXT_COMMANDS,
    ],
    ids=lambda spec: "-".join(spec.command),
)
def test_no_local_dagster_components_failure(spec: CommandSpec) -> None:
    with ProxyRunner.test() as runner, isolated_components_venv(runner):
        _uninstall_dagster_components_from_local_venv(Path.cwd())
        result = runner.invoke(*spec.to_cli_args())
        assert_runner_result(result, exit_0=False)
        assert (
            "Could not find the `dagster-components` executable in the virtual environment"
            in result.output
        )


@pytest.mark.parametrize(
    "spec",
    [
        *COMPONENT_LIBRARY_CONTEXT_COMMANDS,
        *REGISTRY_CONTEXT_COMMANDS,
        *CODE_LOCATION_CONTEXT_COMMANDS,
    ],
    ids=lambda spec: "-".join(spec.command),
)
def test_no_ambient_dagster_components_failure(spec: CommandSpec) -> None:
    with ProxyRunner.test() as runner, runner.isolated_filesystem():
        cli_args = _add_global_cli_options(spec.to_cli_args(), "--no-require-local-venv")
        # Set $PATH to /dev/null to ensure that the `dagster-components` executable is not found
        result = runner.invoke(*cli_args, "--no-require-local-venv", env={"PATH": "/dev/null"})
        assert_runner_result(result, exit_0=False)
        assert "Could not find the `dagster-components` executable" in result.output


@pytest.mark.parametrize(
    "spec", CODE_LOCATION_CONTEXT_COMMANDS, ids=lambda spec: "-".join(spec.command)
)
def test_no_code_location_failure(spec: CommandSpec) -> None:
    with ProxyRunner.test() as runner, isolated_components_venv(runner):
        result = runner.invoke(*spec.to_cli_args())
        assert_runner_result(result, exit_0=False)
        assert "must be run inside a Dagster code location directory" in result.output


@pytest.mark.parametrize(
    "spec", COMPONENT_LIBRARY_CONTEXT_COMMANDS, ids=lambda spec: "-".join(spec.command)
)
def test_no_component_library_failure(spec: CommandSpec) -> None:
    with ProxyRunner.test() as runner, isolated_components_venv(runner):
        result = runner.invoke(*spec.to_cli_args())
        assert_runner_result(result, exit_0=False)
        assert "must be run inside a Dagster component library directory" in result.output


@pytest.mark.parametrize(
    "spec", DEPLOYMENT_CONTEXT_COMMANDS, ids=lambda spec: "-".join(spec.command)
)
def test_no_deployment_failure(spec: CommandSpec) -> None:
    with ProxyRunner.test() as runner, isolated_components_venv(runner):
        result = runner.invoke(*spec.to_cli_args())
        assert_runner_result(result, exit_0=False)
        assert "must be run inside a Dagster deployment directory" in result.output


@pytest.mark.parametrize(
    "spec", DEPLOYMENT_OR_CODE_LOCATION_CONTEXT_COMMANDS, ids=lambda spec: "-".join(spec.command)
)
def test_no_deployment_or_code_location_failure(spec: CommandSpec) -> None:
    with ProxyRunner.test() as runner, isolated_components_venv(runner):
        result = runner.invoke(*spec.to_cli_args())
        assert_runner_result(result, exit_0=False)
        assert "must be run inside a Dagster deployment or code location directory" in result.output


# ########################
# ##### HELPERS
# ########################


# `dg component scaffold` is special because global options have to be inserted before the
# subcommand name, instead of just at the end.
def _add_global_cli_options(cli_args: tuple[str, ...], *global_opts: str) -> list[str]:
    if cli_args[:2] == ("component", "scaffold"):
        return [*cli_args[:2], *global_opts, *cli_args[2:]]
    else:
        return [*cli_args, *global_opts]


def _uninstall_dagster_components_from_local_venv(path: Path) -> None:
    local_venv = resolve_local_venv(Path.cwd())
    assert local_venv, f"No local venv resolvable from {path}"
    subprocess.check_output(
        [
            "uv",
            "pip",
            "uninstall",
            "--python",
            str(get_venv_executable(local_venv)),
            "dagster-components",
        ],
    )
