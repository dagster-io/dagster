import os
import subprocess

import pytest
from automation import git


@pytest.fixture(name="repo")
def repo_fixture(tmpdir):
    root = (tmpdir / "repo").mkdir()
    with root.as_cwd():
        subprocess.call(["git", "init", "-q"])
        (root / "subdir").mkdir()

    return root


@pytest.fixture(name="other_repo")
def other_repo_fixture(tmpdir):
    root = (tmpdir / "other_repo").mkdir()
    with root.as_cwd():
        subprocess.call(["git", "init", "-q"])
        (root / "subdir").mkdir()

    return root


def test_git_repo_root(repo, other_repo):
    with repo.as_cwd():
        assert git.git_repo_root() == str(repo)
        assert git.git_repo_root(other_repo) == str(other_repo)
        assert git.git_repo_root(str(other_repo)) == str(other_repo)
        assert git.git_repo_root(other_repo / "subdir") == str(other_repo)
        assert git.git_repo_root(str(other_repo / "subdir")) == str(other_repo)

        # The directory doesn't exist
        with pytest.raises(Exception):
            git.git_repo_root("/foo/bar/baz")
        assert os.getcwd() == repo

    with (repo / "subdir").as_cwd():
        assert git.git_repo_root() == str(repo)
        assert git.git_repo_root(str(other_repo)) == str(other_repo)
        assert git.git_repo_root(other_repo / "subdir") == str(other_repo)
        assert git.git_repo_root(str(other_repo / "subdir")) == str(other_repo)


def test_git_repo_errors(repo):
    with repo.as_cwd():
        # If the path doesn't exist, we still remain
        # in the original cwd
        with pytest.raises(FileNotFoundError):
            git.git_repo_root("/foo/bar/baz")
        assert os.getcwd() == repo

        # If the path isn't part of a git repo
        # we still remain in the original cwd
        with pytest.raises(subprocess.CalledProcessError):
            git.git_repo_root("/tmp")
        assert os.getcwd() == repo
