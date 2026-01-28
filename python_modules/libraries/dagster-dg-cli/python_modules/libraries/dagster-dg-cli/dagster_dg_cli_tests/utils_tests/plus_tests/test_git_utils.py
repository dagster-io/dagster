"""Tests for git utility functions used in branch deployment commands."""

import subprocess
import tempfile
from pathlib import Path

import pytest
from dagster_dg_cli.utils.plus.git_utils import (
    find_git_repo_root,
    get_git_metadata_for_branch_deployment,
    get_local_branch_name,
    get_local_repo_name,
    read_git_commit_metadata,
)


@pytest.fixture
def temp_git_repo():
    """Create a temporary git repository for testing."""
    with tempfile.TemporaryDirectory() as tmpdir:
        repo_path = Path(tmpdir)

        # Initialize git repo
        subprocess.run(["git", "init"], cwd=repo_path, check=True, capture_output=True)
        subprocess.run(
            ["git", "config", "user.email", "test@example.com"],
            cwd=repo_path,
            check=True,
            capture_output=True,
        )
        subprocess.run(
            ["git", "config", "user.name", "Test User"],
            cwd=repo_path,
            check=True,
            capture_output=True,
        )

        # Add a remote
        subprocess.run(
            ["git", "remote", "add", "origin", "git@github.com:dagster-io/dagster.git"],
            cwd=repo_path,
            check=True,
            capture_output=True,
        )

        # Create initial commit
        (repo_path / "test.txt").write_text("test content")
        subprocess.run(["git", "add", "."], cwd=repo_path, check=True, capture_output=True)
        subprocess.run(
            ["git", "commit", "-m", "Initial commit"],
            cwd=repo_path,
            check=True,
            capture_output=True,
        )

        yield repo_path


def test_find_git_repo_root_success(temp_git_repo):
    """Test finding git repo root from various subdirectories."""
    # Create nested directories
    nested = temp_git_repo / "a" / "b" / "c"
    nested.mkdir(parents=True)

    # Should find root from nested directory
    found_root = find_git_repo_root(nested)
    assert found_root.resolve() == temp_git_repo.resolve()


def test_find_git_repo_root_from_root(temp_git_repo):
    """Test finding git repo root from the root itself."""
    found_root = find_git_repo_root(temp_git_repo)
    assert found_root.resolve() == temp_git_repo.resolve()


def test_find_git_repo_root_no_repo():
    """Test error when not in a git repository."""
    with tempfile.TemporaryDirectory() as tmpdir:
        with pytest.raises(Exception) as exc_info:
            find_git_repo_root(Path(tmpdir))
        assert "No git repository found" in str(exc_info.value)


def test_get_local_repo_name_ssh_url(temp_git_repo):
    """Test extracting repo name from SSH URL."""
    repo_name = get_local_repo_name(temp_git_repo)
    assert repo_name == "dagster-io/dagster"


def test_get_local_repo_name_https_url(temp_git_repo):
    """Test extracting repo name from HTTPS URL."""
    # Change remote to HTTPS URL
    subprocess.run(
        ["git", "remote", "set-url", "origin", "https://github.com/dagster-io/dagster.git"],
        cwd=temp_git_repo,
        check=True,
        capture_output=True,
    )

    repo_name = get_local_repo_name(temp_git_repo)
    assert repo_name == "dagster-io/dagster"


def test_get_local_repo_name_without_git_extension(temp_git_repo):
    """Test extracting repo name from URL without .git extension."""
    subprocess.run(
        ["git", "remote", "set-url", "origin", "https://github.com/dagster-io/dagster"],
        cwd=temp_git_repo,
        check=True,
        capture_output=True,
    )

    repo_name = get_local_repo_name(temp_git_repo)
    assert repo_name == "dagster-io/dagster"


def test_get_local_repo_name_no_remote():
    """Test error when no remote is configured."""
    with tempfile.TemporaryDirectory() as tmpdir:
        repo_path = Path(tmpdir)
        subprocess.run(["git", "init"], cwd=repo_path, check=True, capture_output=True)

        with pytest.raises(Exception) as exc_info:
            get_local_repo_name(repo_path)
        assert "Could not determine repo name" in str(exc_info.value)


def test_get_local_branch_name_success(temp_git_repo):
    """Test getting current branch name."""
    branch_name = get_local_branch_name(temp_git_repo)
    # Default branch is usually 'master' or 'main'
    assert branch_name in ["master", "main"]


def test_get_local_branch_name_custom_branch(temp_git_repo):
    """Test getting branch name on a custom branch."""
    # Create and checkout a new branch
    subprocess.run(
        ["git", "checkout", "-b", "feature-branch"],
        cwd=temp_git_repo,
        check=True,
        capture_output=True,
    )

    branch_name = get_local_branch_name(temp_git_repo)
    assert branch_name == "feature-branch"


def test_get_local_branch_name_detached_head(temp_git_repo):
    """Test error when in detached HEAD state."""
    # Get commit hash and checkout to detached HEAD
    result = subprocess.run(
        ["git", "rev-parse", "HEAD"],
        cwd=temp_git_repo,
        check=True,
        capture_output=True,
        text=True,
    )
    commit_hash = result.stdout.strip()

    subprocess.run(
        ["git", "checkout", commit_hash],
        cwd=temp_git_repo,
        check=True,
        capture_output=True,
    )

    with pytest.raises(Exception) as exc_info:
        get_local_branch_name(temp_git_repo)
    assert "detached HEAD" in str(exc_info.value)


def test_read_git_commit_metadata_success(temp_git_repo):
    """Test reading commit metadata from git log."""
    metadata = read_git_commit_metadata(temp_git_repo)

    assert "commit_hash" in metadata
    assert "author_email" in metadata
    assert "author_name" in metadata
    assert "timestamp" in metadata
    assert "commit_message" in metadata

    # Verify types
    assert isinstance(metadata["commit_hash"], str)
    assert isinstance(metadata["author_email"], str)
    assert isinstance(metadata["author_name"], str)
    assert isinstance(metadata["timestamp"], float)
    assert isinstance(metadata["commit_message"], str)

    # Verify values from our test commit
    assert metadata["author_email"] == "test@example.com"
    assert metadata["author_name"] == "Test User"
    assert metadata["commit_message"] == "Initial commit"


def test_read_git_commit_metadata_no_commits():
    """Test error when repository has no commits."""
    with tempfile.TemporaryDirectory() as tmpdir:
        repo_path = Path(tmpdir)
        subprocess.run(["git", "init"], cwd=repo_path, check=True, capture_output=True)

        with pytest.raises(Exception) as exc_info:
            read_git_commit_metadata(repo_path)
        assert "Could not read git state" in str(exc_info.value)


def test_get_git_metadata_for_branch_deployment_with_git_state(temp_git_repo):
    """Test getting complete git metadata including commit info."""
    repo_root, repo_name, branch_name, commit_metadata = get_git_metadata_for_branch_deployment(
        temp_git_repo, read_git_state=True
    )

    assert repo_root.resolve() == temp_git_repo.resolve()
    assert repo_name == "dagster-io/dagster"
    assert branch_name in ["master", "main"]
    assert commit_metadata is not None
    assert "commit_hash" in commit_metadata
    assert "timestamp" in commit_metadata


def test_get_git_metadata_for_branch_deployment_without_git_state(temp_git_repo):
    """Test getting git metadata without reading commit info."""
    repo_root, repo_name, branch_name, commit_metadata = get_git_metadata_for_branch_deployment(
        temp_git_repo, read_git_state=False
    )

    assert repo_root.resolve() == temp_git_repo.resolve()
    assert repo_name == "dagster-io/dagster"
    assert branch_name in ["master", "main"]
    assert commit_metadata is None


def test_get_git_metadata_for_branch_deployment_from_nested_dir(temp_git_repo):
    """Test getting git metadata from a nested directory."""
    nested = temp_git_repo / "nested" / "dir"
    nested.mkdir(parents=True)

    repo_root, repo_name, branch_name, commit_metadata = get_git_metadata_for_branch_deployment(
        nested, read_git_state=False
    )

    assert repo_root.resolve() == temp_git_repo.resolve()
    assert repo_name == "dagster-io/dagster"


def test_get_git_metadata_for_branch_deployment_no_repo():
    """Test error when not in a git repository."""
    with tempfile.TemporaryDirectory() as tmpdir:
        with pytest.raises(Exception) as exc_info:
            get_git_metadata_for_branch_deployment(Path(tmpdir), read_git_state=False)
        assert "No git repository found" in str(exc_info.value)
