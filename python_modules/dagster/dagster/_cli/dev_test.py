import os
import subprocess
import sys
import tempfile
from pathlib import Path

import pytest
from click.testing import CliRunner

from dagster._cli.dev import dev_command


@pytest.fixture
def temp_project_dir():
    with tempfile.TemporaryDirectory() as temp_dir:
        yield temp_dir


def test_dev_command_with_project(temp_project_dir):
    runner = CliRunner()
    result = runner.invoke(dev_command, ["--project", temp_project_dir])
    assert result.exit_code == 0
    assert "DAGSTER_PROJECT" in os.environ
    assert os.environ["DAGSTER_PROJECT"] == temp_project_dir


def test_dev_command_without_project():
    runner = CliRunner()
    result = runner.invoke(dev_command)
    assert result.exit_code == 0
    assert "DAGSTER_PROJECT" not in os.environ
