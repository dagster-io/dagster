import os
import tempfile
from pathlib import Path

import pytest
from click.testing import CliRunner

from dagster._cli.project import scaffold_command


@pytest.fixture
def temp_project_dir():
    with tempfile.TemporaryDirectory() as temp_dir:
        yield temp_dir


def test_scaffold_command_success_message(temp_project_dir):
    runner = CliRunner()
    project_name = "test_project"
    result = runner.invoke(scaffold_command, ["--name", project_name])
    assert result.exit_code == 0
    assert f"dagster dev --project {project_name}" in result.output
