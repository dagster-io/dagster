import os

from .utils import tempdir_wrapper


def test_tempdir_wrapper():
    with tempdir_wrapper("/tmp/foobar") as tempfile:
        assert tempfile == "/tmp/foobar"

    with tempdir_wrapper() as tempfile:
        assert os.path.isdir(tempfile)
    assert not os.path.isdir(tempfile)
