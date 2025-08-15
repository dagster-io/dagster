"""Tests for git and GitHub helper functions used by scaffold branch command."""

import os
import subprocess
from pathlib import Path
from tempfile import TemporaryDirectory
from unittest.mock import Mock, patch

import pytest
from dagster_dg_cli.cli.scaffold.branch import (
    create_branch_and_pr,
    create_empty_commit,
    create_git_branch,
    has_remote_origin,
)


# Helper functions for git operations in tests
def git_init(repo_path: Path) -> None:
    """Initialize a git repository."""
    subprocess.run(["git", "init"], cwd=repo_path, check=True, capture_output=True)


def git_config_user(
    repo_path: Path, email: str = "test@example.com", name: str = "Test User"
) -> None:
    """Configure git user email and name."""
    subprocess.run(
        ["git", "config", "user.email", email], cwd=repo_path, check=True, capture_output=True
    )
    subprocess.run(
        ["git", "config", "user.name", name], cwd=repo_path, check=True, capture_output=True
    )


def git_initial_commit(repo_path: Path) -> None:
    """Create an empty initial commit."""
    subprocess.run(
        ["git", "commit", "--allow-empty", "-m", "Initial"],
        cwd=repo_path,
        check=True,
        capture_output=True,
    )


def git_add_remote(repo_path: Path, remote_path: Path, remote_name: str = "origin") -> None:
    """Add a git remote."""
    subprocess.run(
        ["git", "remote", "add", remote_name, str(remote_path)],
        cwd=repo_path,
        check=True,
        capture_output=True,
    )


def git_set_main_branch(repo_path: Path) -> None:
    """Set the main branch name."""
    subprocess.run(["git", "branch", "-M", "main"], cwd=repo_path, check=True, capture_output=True)


def git_push_to_remote(repo_path: Path, branch: str = "main", remote: str = "origin") -> None:
    """Push branch to remote."""
    subprocess.run(
        ["git", "push", "-u", remote, branch], cwd=repo_path, check=True, capture_output=True
    )


def setup_basic_git_repo(repo_path: Path) -> None:
    """Set up a basic git repository with initial commit."""
    git_init(repo_path)
    git_config_user(repo_path)
    git_initial_commit(repo_path)


def setup_git_repo_with_remote(local_path: Path, remote_path: Path) -> None:
    """Set up a git repository with a remote."""
    # Create bare remote
    subprocess.run(["git", "init", "--bare"], cwd=remote_path, check=True, capture_output=True)

    # Set up local repo
    git_init(local_path)
    git_config_user(local_path)
    git_add_remote(local_path, remote_path)
    git_initial_commit(local_path)
    git_set_main_branch(local_path)
    git_push_to_remote(local_path)


@pytest.fixture
def git_repo():
    """Create a real git repository for testing."""
    with TemporaryDirectory() as tmpdir:
        repo_path = Path(tmpdir)
        setup_basic_git_repo(repo_path)
        yield repo_path


@pytest.fixture
def git_repo_with_remote():
    """Create a git repository with a fake remote."""
    with TemporaryDirectory() as tmpdir:
        remote_path = Path(tmpdir) / "remote.git"
        remote_path.mkdir()

        local_path = Path(tmpdir) / "local"
        local_path.mkdir()

        setup_git_repo_with_remote(local_path, remote_path)
        yield local_path


@pytest.mark.integration
class TestGitOperations:
    """Test actual git operations."""

    def test_create_branch_in_real_repo(self, git_repo):
        """Test branch creation with real git."""
        original_dir = os.getcwd()
        try:
            os.chdir(git_repo)

            # Create branch
            commit_hash = create_git_branch("test-feature")

            # Verify branch was created
            result = subprocess.run(
                ["git", "branch", "--show-current"],
                capture_output=True,
                text=True,
                cwd=git_repo,
                check=False,
            )
            assert result.stdout.strip() == "test-feature"
            assert len(commit_hash) == 40  # Git SHA-1 hash length

            # Verify we can create another branch
            commit_hash2 = create_git_branch("another-feature")
            result = subprocess.run(
                ["git", "branch", "--show-current"],
                capture_output=True,
                text=True,
                cwd=git_repo,
                check=False,
            )
            assert result.stdout.strip() == "another-feature"
            assert len(commit_hash2) == 40
        finally:
            os.chdir(original_dir)

    def test_create_empty_commit(self, git_repo):
        """Test empty commit creation."""
        original_dir = os.getcwd()
        try:
            os.chdir(git_repo)

            # Get initial commit count
            before = subprocess.run(
                ["git", "rev-list", "--count", "HEAD"],
                capture_output=True,
                text=True,
                cwd=git_repo,
                check=False,
            )
            before_count = int(before.stdout.strip())

            # Create empty commit
            create_empty_commit("Test commit message")

            # Verify commit was created
            after = subprocess.run(
                ["git", "rev-list", "--count", "HEAD"],
                capture_output=True,
                text=True,
                cwd=git_repo,
                check=False,
            )
            after_count = int(after.stdout.strip())
            assert after_count == before_count + 1

            # Check commit message
            last_msg = subprocess.run(
                ["git", "log", "-1", "--pretty=%B"],
                capture_output=True,
                text=True,
                cwd=git_repo,
                check=False,
            )
            assert last_msg.stdout.strip() == "Test commit message"
        finally:
            os.chdir(original_dir)

    def test_has_remote_origin_true(self, git_repo_with_remote):
        """Test has_remote_origin returns True when remote exists."""
        original_dir = os.getcwd()
        try:
            os.chdir(git_repo_with_remote)
            assert has_remote_origin() is True
        finally:
            os.chdir(original_dir)

    def test_has_remote_origin_false(self, git_repo):
        """Test has_remote_origin returns False when no remote exists."""
        original_dir = os.getcwd()
        try:
            os.chdir(git_repo)
            assert has_remote_origin() is False
        finally:
            os.chdir(original_dir)


@pytest.mark.integration
class TestGitWithGitHub:
    """Test git operations with GitHub integration."""

    @patch("dagster_dg_cli.cli.scaffold.branch._run_gh_command")
    def test_branch_and_pr_workflow(self, mock_gh, git_repo_with_remote):
        """Test full branch creation and PR workflow."""
        mock_gh.return_value = Mock(
            returncode=0, stdout="https://github.com/user/repo/pull/123", stderr=""
        )

        original_dir = os.getcwd()
        try:
            os.chdir(git_repo_with_remote)

            # Create branch
            create_git_branch("new-feature")

            # Create empty commit
            create_empty_commit("Initial commit for new-feature branch")

            # Create PR
            pr_url = create_branch_and_pr(
                "new-feature", "New Feature", "This is a test PR", local_only=False
            )

            assert pr_url == "https://github.com/user/repo/pull/123"

            # Verify branch exists in git
            branches = subprocess.run(
                ["git", "branch"],
                capture_output=True,
                text=True,
                cwd=git_repo_with_remote,
                check=False,
            )
            assert "new-feature" in branches.stdout

            # Verify push was attempted (branch should exist on remote)
            remote_branches = subprocess.run(
                ["git", "branch", "-r"],
                capture_output=True,
                text=True,
                cwd=git_repo_with_remote,
                check=False,
            )
            assert "origin/new-feature" in remote_branches.stdout

            # Verify gh was called correctly
            mock_gh.assert_called_once_with(
                ["pr", "create", "--title", "New Feature", "--body", "This is a test PR"]
            )
        finally:
            os.chdir(original_dir)

    def test_local_only_workflow(self, git_repo):
        """Test branch creation without remote push."""
        original_dir = os.getcwd()
        try:
            os.chdir(git_repo)

            # Create branch
            create_git_branch("local-feature")

            # Create empty commit
            create_empty_commit("Initial commit for local-feature branch")

            # Create PR with local_only=True
            pr_url = create_branch_and_pr(
                "local-feature", "Local Feature", "This is a local branch", local_only=True
            )

            assert pr_url == ""

            # Verify branch exists locally
            branches = subprocess.run(
                ["git", "branch"], capture_output=True, text=True, cwd=git_repo, check=False
            )
            assert "local-feature" in branches.stdout

            # Verify no remote exists (should not have pushed)
            assert has_remote_origin() is False
        finally:
            os.chdir(original_dir)
