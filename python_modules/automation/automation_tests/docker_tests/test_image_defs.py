import subprocess

import pytest
from automation.docker.image_defs import copy_directories, get_image


@pytest.fixture(name="repo")
def repo_fixture(tmpdir):
    root = (tmpdir / "repo").mkdir()
    with root.as_cwd():
        subprocess.call(["git", "init", "-q"])

    return root


def test_copy_directories(tmpdir, repo):
    with tmpdir.as_cwd():
        filename = "hello_world.txt"
        (repo / filename).write("Hello, world!")
        destination = "build_cache"

        with copy_directories([filename], repo, destination=destination):
            assert (repo / destination / filename).exists()
        assert not (repo / destination).exists()

        with pytest.raises(Exception):
            with copy_directories(["bad file"], repo, destination=destination):
                pass
        assert not (repo / destination).exists()


def test_get_image(tmpdir):
    assert get_image("k8s-example")

    with pytest.raises(Exception) as e:
        get_image("hello-world", images_path=tmpdir)
    assert "could not find image hello-world" in str(e.value)

    hello_world = tmpdir / "hello-world"
    hello_world.mkdir()
    (hello_world / "Dockerfile").write("FROM hello-world")

    image = get_image("hello-world", images_path=tmpdir)
    assert image.image == "hello-world"
    assert image.path == hello_world
