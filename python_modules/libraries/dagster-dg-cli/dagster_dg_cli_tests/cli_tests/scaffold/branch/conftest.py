"""Shared fixtures for branch command tests."""

import subprocess
from pathlib import Path
from tempfile import TemporaryDirectory

import pytest


@pytest.fixture
def basic_git_repo():
    """Provides a basic initialized git repository."""
    with TemporaryDirectory() as tmpdir:
        repo_path = Path(tmpdir)
        subprocess.run(["git", "init"], cwd=repo_path, check=True, capture_output=True)
        subprocess.run(
            ["git", "config", "user.email", "test@test.com"],
            cwd=repo_path,
            check=True,
            capture_output=True,
        )
        subprocess.run(
            ["git", "config", "user.name", "Test"], cwd=repo_path, check=True, capture_output=True
        )
        yield repo_path


@pytest.fixture
def mock_github_api():
    """Provides a mock for GitHub API calls."""
    from unittest.mock import Mock

    mock = Mock()
    mock.create_pr.return_value = "https://github.com/test/repo/pull/1"
    return mock
