import pytest
from automation.docker.image_defs import get_image


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
