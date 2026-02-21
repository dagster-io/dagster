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


def _git(repo_path: Path, *args: str, text: bool = False) -> subprocess.CompletedProcess:
    return subprocess.run(
        ["git", *args],
        cwd=repo_path,
        check=True,
        capture_output=True,
        text=text,
    )


@pytest.fixture
def temp_git_repo():
    """Create a temporary git repository for testing."""
    with tempfile.TemporaryDirectory() as tmpdir:
        repo_path = Path(tmpdir)

        _git(repo_path, "init")
        _git(repo_path, "config", "user.email", "test@example.com")
        _git(repo_path, "config", "user.name", "Test User")
        _git(repo_path, "remote", "add", "origin", "git@github.com:dagster-io/dagster.git")

        (repo_path / "test.txt").write_text("test content")
        _git(repo_path, "add", ".")
        _git(repo_path, "commit", "-m", "Initial commit")

        yield repo_path


def test_find_git_repo_root_success(temp_git_repo):
    nested = temp_git_repo / "a" / "b" / "c"
    nested.mkdir(parents=True)

    found_root = find_git_repo_root(nested)
    assert found_root.resolve() == temp_git_repo.resolve()


def test_find_git_repo_root_from_root(temp_git_repo):
    found_root = find_git_repo_root(temp_git_repo)
    assert found_root.resolve() == temp_git_repo.resolve()


def test_find_git_repo_root_no_repo():
    with tempfile.TemporaryDirectory() as tmpdir:
        with pytest.raises(Exception) as exc_info:
            find_git_repo_root(Path(tmpdir))
        assert "No git repository found" in str(exc_info.value)


@pytest.mark.parametrize(
    "remote_url",
    [
        "git@github.com:dagster-io/dagster.git",
        "https://github.com/dagster-io/dagster.git",
        "https://github.com/dagster-io/dagster",
    ],
)
def test_get_local_repo_name_supported_urls(temp_git_repo, remote_url):
    _git(temp_git_repo, "remote", "set-url", "origin", remote_url)
    assert get_local_repo_name(temp_git_repo) == "dagster-io/dagster"


def test_get_local_repo_name_no_remote():
    with tempfile.TemporaryDirectory() as tmpdir:
        repo_path = Path(tmpdir)
        _git(repo_path, "init")

        with pytest.raises(Exception) as exc_info:
            get_local_repo_name(repo_path)
        assert "Could not determine repo name" in str(exc_info.value)


def test_get_local_branch_name_success(temp_git_repo):
    branch_name = get_local_branch_name(temp_git_repo)
    assert branch_name in ["master", "main"]


def test_get_local_branch_name_custom_branch(temp_git_repo):
    _git(temp_git_repo, "checkout", "-b", "feature-branch")
    assert get_local_branch_name(temp_git_repo) == "feature-branch"


def test_get_local_branch_name_detached_head(temp_git_repo):
    commit_hash = _git(temp_git_repo, "rev-parse", "HEAD", text=True).stdout.strip()
    _git(temp_git_repo, "checkout", commit_hash)

    with pytest.raises(Exception) as exc_info:
        get_local_branch_name(temp_git_repo)
    assert "detached HEAD" in str(exc_info.value)


def test_read_git_commit_metadata_success(temp_git_repo):
    metadata = read_git_commit_metadata(temp_git_repo)

    assert metadata["author_email"] == "test@example.com"
    assert metadata["author_name"] == "Test User"
    assert metadata["commit_message"] == "Initial commit"
    assert isinstance(metadata["commit_hash"], str)
    assert isinstance(metadata["timestamp"], float)


def test_read_git_commit_metadata_no_commits():
    with tempfile.TemporaryDirectory() as tmpdir:
        repo_path = Path(tmpdir)
        _git(repo_path, "init")

        with pytest.raises(Exception) as exc_info:
            read_git_commit_metadata(repo_path)
        assert "Could not read git state" in str(exc_info.value)


def test_get_git_metadata_for_branch_deployment_with_git_state(temp_git_repo):
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
    repo_root, repo_name, branch_name, commit_metadata = get_git_metadata_for_branch_deployment(
        temp_git_repo, read_git_state=False
    )

    assert repo_root.resolve() == temp_git_repo.resolve()
    assert repo_name == "dagster-io/dagster"
    assert branch_name in ["master", "main"]
    assert commit_metadata is None


def test_get_git_metadata_for_branch_deployment_from_nested_dir(temp_git_repo):
    nested = temp_git_repo / "nested" / "dir"
    nested.mkdir(parents=True)

    repo_root, repo_name, _branch_name, _commit_metadata = get_git_metadata_for_branch_deployment(
        nested, read_git_state=False
    )

    assert repo_root.resolve() == temp_git_repo.resolve()
    assert repo_name == "dagster-io/dagster"


def test_get_git_metadata_for_branch_deployment_no_repo():
    with tempfile.TemporaryDirectory() as tmpdir:
        with pytest.raises(Exception) as exc_info:
            get_git_metadata_for_branch_deployment(Path(tmpdir), read_git_state=False)
        assert "No git repository found" in str(exc_info.value)
