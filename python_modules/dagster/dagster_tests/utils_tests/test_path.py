import os
import subprocess
import tempfile
from pathlib import Path

import pytest
from dagster._utils.path import is_likely_venv_executable


@pytest.fixture
def temp_venv():
    with tempfile.TemporaryDirectory() as temp_dir:
        temp_dir_venv = Path(temp_dir) / "venv"
        try:
            # Check if uv is installed
            subprocess.run(["uv", "--version"], check=True, capture_output=True)
        except (subprocess.CalledProcessError, FileNotFoundError):
            raise Exception("uv is not installed or not in PATH")

        # Create a new virtual environment using uv
        result = subprocess.run(
            ["uv", "venv", temp_dir_venv, "--seed"], check=True, capture_output=True, text=True
        )
        assert result.returncode == 0, f"Failed to create virtual environment: {result.stderr}"

        python_executable = temp_dir_venv / "bin" / "python"
        yield python_executable


def test_is_likely_venv_executable(temp_venv):
    assert is_likely_venv_executable(temp_venv)
    with tempfile.TemporaryDirectory() as temp_dir:
        assert not is_likely_venv_executable(os.path.join(temp_dir, "python"))
