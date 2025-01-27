from collections.abc import Sequence
from typing import Optional

import pytest
from click.testing import CliRunner
from dagster._cli.definitions import definitions_validate_command
from dagster._utils import file_relative_path

EMPTY_PROJECT_PATH = file_relative_path(__file__, "definitions_command_projects/empty_project")
VALID_PROJECT_PATH = file_relative_path(__file__, "definitions_command_projects/valid_project")
INVALID_PROJECT_PATH = file_relative_path(__file__, "definitions_command_projects/invalid_project")


def invoke_validate(options: Optional[Sequence[str]] = None):
    runner = CliRunner()
    return runner.invoke(definitions_validate_command, options)


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
    ],
)
def test_valid_project(options, monkeypatch):
    with monkeypatch.context() as m:
        m.chdir(VALID_PROJECT_PATH)
        result = invoke_validate(options=options)
        assert result.exit_code == 0
        assert "Validation successful" in result.output


def test_valid_project_with_multiple_definitions_files(monkeypatch):
    with monkeypatch.context() as m:
        m.chdir(VALID_PROJECT_PATH)
        options = ["-f", "valid_project/definitions.py", "-f", "valid_project/more_definitions.py"]
        result = invoke_validate(options=options)
        assert result.exit_code == 0
        assert "Validation successful for code location definitions.py." in result.output
        assert "Validation successful for code location more_definitions.py." in result.output


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


def test_env_var(monkeypatch):
    with monkeypatch.context() as m:
        m.chdir(VALID_PROJECT_PATH)
        # Definitions in `gated_definitions.py` are gated by the "DAGSTER_IS_DEFS_VALIDATION_CLI" environment variable
        result = invoke_validate(options=["-f", "valid_project/gated_definitions.py"])
        assert result.exit_code == 0
        assert "Validation successful for code location gated_definitions.py." in result.output
