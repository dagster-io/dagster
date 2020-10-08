import contextlib
from tempfile import NamedTemporaryFile

import pytest
import six


@pytest.fixture(scope="function")
def tmp_file(tmpdir):
    @contextlib.contextmanager
    def _tmp_file_cm(file_contents):
        with NamedTemporaryFile(dir=str(tmpdir)) as f:
            f.write(six.ensure_binary(file_contents))
            f.flush()
            yield str(tmpdir), f.name

    return _tmp_file_cm
