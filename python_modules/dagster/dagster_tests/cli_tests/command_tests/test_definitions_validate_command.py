from collections.abc import Sequence
from typing import Optional

import pytest
from click.testing import CliRunner
from dagster._cli.definitions import definitions_validate_command
from dagster._utils import file_relative_path, pushd

EMPTY_PROJECT_PATH = file_relative_path(__file__, "definitions_command_projects/empty_project")
VALID_PROJECT_PATH = file_relative_path(__file__, "definitions_command_projects/valid_project")
INVALID_PROJECT_PATH = file_relative_path(__file__, "definitions_command_projects/invalid_project")
INVALID_PROJECT_PATH_WITH_EXCEPTION = file_relative_path(
    __file__, "definitions_command_projects/invalid_project_exc"
)
PROJECT_ALTERNATE_ENTRYPOINT_PATH = file_relative_path(
    __file__, "definitions_command_projects/alternate_entrypoint_project"
)


def invoke_validate(options: Optional[Sequence[str]] = None, log_level: str = "DEBUG"):
    runner = CliRunner()
    return runner.invoke(
        definitions_validate_command, list(options or []) + ["--log-level", log_level]
    )


def test_empty_project(monkeypatch):
    with monkeypatch.context() as m:
        m.chdir(EMPTY_PROJECT_PATH)
        result = invoke_validate()
        assert result.exit_code == 2
        assert (
            "Error: No arguments given and no [tool.dagster] block in pyproject.toml found."
            in result.output
        )


@pytest.mark.parametrize(
    "options",
    [
        [],
        ["-f", "valid_project/definitions.py"],
        ["-f", "valid_project/definitions.py"],
        ["-m", "valid_project.definitions"],
        ["-w", "workspace.yaml"],
        ["--load-with-grpc"],
    ],
)
def test_valid_project(options, monkeypatch):
    with monkeypatch.context() as m:
        m.chdir(VALID_PROJECT_PATH)
        result = invoke_validate(options=options)
        assert result.exit_code == 0
        assert "Validation successful" in result.output

        if "--load-with-grpc" in options:
            assert "Loading workspace with gRPC server" in result.output
        else:
            assert "Loading workspace in-process" in result.output


def test_alternate_entrypoint(monkeypatch):
    with monkeypatch.context() as m:
        m.chdir(PROJECT_ALTERNATE_ENTRYPOINT_PATH)
        result = invoke_validate(
            options=["-w", "workspace.yaml"],
        )

        # Since we're using an alternate entrypoint, we always load with gRPC
        assert "Loading workspace with gRPC server" in result.output


def test_valid_project_with_multiple_definitions_files(monkeypatch):
    with monkeypatch.context() as m:
        m.chdir(VALID_PROJECT_PATH)
        options = [
            "-f",
            "valid_project/definitions.py",
            "-f",
            "valid_project/more_definitions.py",
        ]
        result = invoke_validate(options=options)
        assert result.exit_code == 0
        assert "Validation successful for code location definitions.py." in result.output
        assert "Validation successful for code location more_definitions.py." in result.output

        # We always load with gRPC when multiple files are provided
        assert "Loading workspace in-process" not in result.output
        assert "Loading workspace with gRPC server" in result.output


@pytest.mark.parametrize(
    "options",
    [
        [],
        ["-f", "invalid_project/definitions.py"],
        ["-m", "invalid_project.definitions"],
        ["-w", "workspace.yaml"],
    ],
)
def test_invalid_project(options, monkeypatch):
    with monkeypatch.context() as m:
        m.chdir(INVALID_PROJECT_PATH)
        result = invoke_validate(options=options)
        assert result.exit_code == 1
        assert "Validation failed" in result.output
        assert "Duplicate asset key: AssetKey(['my_asset'])" in result.output


@pytest.mark.parametrize("verbose", [True, False])
def test_invalid_project_truncated_properly(verbose):
    with pushd(INVALID_PROJECT_PATH_WITH_EXCEPTION):
        result = invoke_validate(options=["--verbose"] if verbose else [])
        assert result.exit_code == 1
        assert "Validation failed" in result.output
        assert "is not a valid name in Dagster" in result.output, result.output

        if verbose:
            assert "importlib" in result.output, result.output
        else:
            # Assert extraneous lines are removed in two blocs
            assert "importlib" not in result.output, result.output
            # Assert system frames hint is present in the output exactly twice,
            # once for the load error (before user code) and one for the Dagster check validation
            # (after user code)
            assert (
                result.output.count(
                    "dagster system frames hidden, run with --verbose to see the full stack trace"
                )
                == 1
            )
            assert result.output.count("dagster system frames hidden") >= 1


def test_env_var(monkeypatch):
    with monkeypatch.context() as m:
        m.chdir(VALID_PROJECT_PATH)
        # Definitions in `gated_definitions.py` are gated by the "DAGSTER_IS_DEFS_VALIDATION_CLI" environment variable
        result = invoke_validate(options=["-f", "valid_project/gated_definitions.py"])
        assert result.exit_code == 0
        assert "Validation successful for code location gated_definitions.py." in result.output
