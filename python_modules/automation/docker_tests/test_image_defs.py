import pytest
from automation.docker.image_defs import get_image


def test_get_image(tmpdir):
    assert get_image("k8s-example")

    with pytest.raises(Exception) as e:
        get_image("new-image", images_path=tmpdir)
    assert "could not find image new-image" in str(e.value)

    (tmpdir / "new-image").mkdir()
    (tmpdir / "new-image" / "Dockerfile").write("FROM hello-world")

    assert get_image("new-image", images_path=tmpdir)
