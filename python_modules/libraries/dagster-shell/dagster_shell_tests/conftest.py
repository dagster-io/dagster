import contextlib
from tempfile import NamedTemporaryFile

import pytest


@pytest.fixture(scope="function")
def tmp_file(tmpdir):
    @contextlib.contextmanager
    def _tmp_file_cm(file_contents):
        with NamedTemporaryFile(dir=str(tmpdir)) as f:
            f.write(file_contents.encode("utf-8"))
            f.flush()
            yield str(tmpdir), f.name

    return _tmp_file_cm
