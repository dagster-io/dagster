import subprocess

import pytest
from automation.docker.image_defs import copy_directories, get_image


@pytest.fixture(name="repo")
def repo_fixture(tmpdir):
    """Test repo.

    repo/
    ├── .git/
    ├── bar/
    │   └── bar.txt
    └── foo/
        └── foo.txt
    """
    root = (tmpdir / "repo").mkdir()
    with root.as_cwd():
        subprocess.call(["git", "init", "-q"])
        (root / "foo").mkdir()
        (root / "foo" / "foo.txt").write("Hello, foo!")
        (root / "bar").mkdir()
        (root / "bar" / "bar.txt").write("Hello, bar!")

    return root


def test_copy_directories(tmpdir, repo):
    with tmpdir.as_cwd():
        destination = "build_cache"

        # Copy a directory
        with copy_directories(["foo"], repo, destination=destination):
            assert (repo / destination / "foo" / "foo.txt").exists()
            assert not (repo / destination / "bar" / "bar.txt").exists()
        assert not (repo / destination).exists()

        # Copy multiple directories
        with copy_directories(["foo", "bar"], repo, destination=destination):
            assert (repo / destination / "foo" / "foo.txt").exists()
            assert (repo / destination / "bar" / "bar.txt").exists()
        assert not (repo / destination).exists()


def test_copy_directories_does_not_exist(tmpdir, repo):
    with tmpdir.as_cwd():
        destination = "build_cache"

        with pytest.raises(Exception):
            with copy_directories(["bad dir"], repo, destination=destination):
                pass
        assert not (repo / destination).exists()


def test_copy_directories_not_a_git_repo(tmpdir, repo):
    (repo / ".git").remove()

    with tmpdir.as_cwd():
        destination = "build_cache"

        with pytest.raises(Exception):
            with copy_directories(["foo"], repo, destination=destination):
                pass
        assert not (repo / destination).exists()


def test_get_image(tmpdir):
    assert get_image("k8s-example")

    with pytest.raises(Exception) as e:
        get_image("hello-world", images_path=str(tmpdir))
    assert "could not find image hello-world" in str(e.value)

    hello_world = tmpdir / "hello-world"
    hello_world.mkdir()
    (hello_world / "Dockerfile").write("FROM hello-world")

    image = get_image("hello-world", images_path=str(tmpdir))
    assert image.image == "hello-world"
    assert image.path == hello_world
