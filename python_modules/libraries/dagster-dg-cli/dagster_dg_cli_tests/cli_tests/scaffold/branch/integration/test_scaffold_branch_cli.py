"""Tests for the dg scaffold branch CLI command."""

import os
import subprocess
from contextlib import contextmanager
from tempfile import TemporaryDirectory
from unittest.mock import Mock, patch

import pytest
from dagster_test.dg_utils.utils import (
    ProxyRunner,
    assert_runner_result,
    isolated_example_project_foo_bar,
)


# Git helper functions
def setup_basic_git_repo(project_dir):
    """Initialize a basic git repository in the given directory."""
    subprocess.run(["git", "init"], cwd=project_dir, check=True, capture_output=True)
    subprocess.run(["git", "config", "user.name", "Test User"], cwd=project_dir, check=True)
    subprocess.run(["git", "config", "user.email", "test@example.com"], cwd=project_dir, check=True)
    # Create initial commit
    subprocess.run(["git", "add", "."], cwd=project_dir, check=True, capture_output=True)
    subprocess.run(
        ["git", "commit", "-m", "Initial commit"], cwd=project_dir, check=True, capture_output=True
    )


def setup_git_repo_with_remote(project_dir, remote_path):
    """Set up a git repository with a remote."""
    # First set up basic git repo
    setup_basic_git_repo(project_dir)

    # Initialize bare remote repository
    subprocess.run(["git", "init", "--bare"], cwd=remote_path, check=True, capture_output=True)

    # Add remote to local repo
    subprocess.run(
        ["git", "remote", "add", "origin", str(remote_path)], cwd=project_dir, check=True
    )

    # Get the current branch name (could be main or master depending on git version)
    result = subprocess.run(
        ["git", "branch", "--show-current"],
        cwd=project_dir,
        capture_output=True,
        text=True,
        check=True,
    )
    current_branch = result.stdout.strip()

    # Push initial commit to remote
    subprocess.run(
        ["git", "push", "-u", "origin", current_branch],
        cwd=project_dir,
        check=True,
        capture_output=True,
    )


@contextmanager
def isolated_project_with_runner(in_workspace=False):
    """Create an isolated project with a ProxyRunner in a single context manager."""
    with ProxyRunner.test() as runner:
        with isolated_example_project_foo_bar(runner, in_workspace=in_workspace) as project_dir:
            yield runner, project_dir


@pytest.mark.integration
class TestScaffoldBranchCLI:
    """Test the dg scaffold branch CLI command."""

    def test_scaffold_branch_simple_name(self):
        """Test scaffold branch command with a simple branch name."""
        with isolated_project_with_runner() as (runner, project_dir):
            # Initialize git repo in the project
            setup_basic_git_repo(project_dir)

            result = runner.invoke("scaffold", "branch", "my-feature", "--local-only")
            assert_runner_result(result)

            # Check output messages
            assert "Creating new branch: my-feature" in result.output
            assert "Created and checked out new branch: my-feature" in result.output
            assert "Created empty commit: Initial commit for my-feature branch" in result.output
            assert "✅ Successfully created branch: my-feature" in result.output

            # Verify branch was actually created
            branches = subprocess.run(
                ["git", "branch"], capture_output=True, text=True, cwd=project_dir, check=False
            )
            assert "my-feature" in branches.stdout

            # Verify commit was created
            last_msg = subprocess.run(
                ["git", "log", "-1", "--pretty=%B"],
                capture_output=True,
                text=True,
                cwd=project_dir,
                check=False,
            )
            assert "Initial commit for my-feature branch" in last_msg.stdout

    def test_scaffold_branch_whitespace_name(self):
        """Test that branch names are properly sanitized."""
        with isolated_project_with_runner() as (runner, project_dir):
            # Initialize git repo
            setup_basic_git_repo(project_dir)

            result = runner.invoke("scaffold", "branch", "  feature-with-spaces  ", "--local-only")
            assert_runner_result(result)

            # Check that whitespace was trimmed
            assert "Creating new branch: feature-with-spaces" in result.output

            # Verify branch name was trimmed
            branches = subprocess.run(
                ["git", "branch"], capture_output=True, text=True, cwd=project_dir, check=False
            )
            assert "feature-with-spaces" in branches.stdout
            assert "  feature-with-spaces  " not in branches.stdout

    @patch("dagster_dg_cli.cli.scaffold.branch.git.run_gh_command")
    def test_scaffold_branch_with_pr(self, mock_gh):
        """Test scaffold branch with PR creation."""
        mock_gh.return_value = Mock(
            returncode=0, stdout="https://github.com/user/repo/pull/456\n", stderr=""
        )

        with isolated_project_with_runner() as (runner, project_dir):
            # Set up git repo with remote
            remote_path = project_dir.parent / "remote.git"
            remote_path.mkdir()
            setup_git_repo_with_remote(project_dir, remote_path)

            result = runner.invoke("scaffold", "branch", "pr-feature")
            assert_runner_result(result)

            # Check output messages
            assert "Creating new branch: pr-feature" in result.output
            assert "Pushed branch pr-feature to remote" in result.output
            assert "Created pull request: https://github.com/user/repo/pull/456" in result.output
            assert "✅ Successfully created branch and pull request" in result.output

            # Verify gh was called
            mock_gh.assert_called_once()
            args = mock_gh.call_args[0][0]
            assert args[0] == "pr"
            assert args[1] == "create"
            assert "--title" in args
            assert "--body" in args

    def test_scaffold_branch_not_in_git_repo(self):
        """Test that scaffold branch fails gracefully when not in a git repo."""
        with TemporaryDirectory() as tmpdir:
            with ProxyRunner.test() as runner:
                original_dir = os.getcwd()
                try:
                    os.chdir(tmpdir)

                    result = runner.invoke("scaffold", "branch", "test-branch")

                    # Should fail with appropriate error message
                    assert result.exit_code != 0
                    assert "This command must be run within a git repository" in result.output
                    assert "git init" in result.output
                finally:
                    os.chdir(original_dir)
