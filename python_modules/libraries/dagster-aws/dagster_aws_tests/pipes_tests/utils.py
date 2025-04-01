import inspect
import shutil
import textwrap
from collections.abc import Iterator
from contextlib import contextmanager
from tempfile import NamedTemporaryFile
from typing import Any, Callable

_PYTHON_EXECUTABLE = shutil.which("python") or "python"
_S3_TEST_BUCKET = "pipes-testing"
_MOTO_SERVER_PORT = 5193
_MOTO_SERVER_URL = f"http://localhost:{_MOTO_SERVER_PORT}"


@contextmanager
def temp_script(script_fn: Callable[[], Any]) -> Iterator[str]:
    # drop the signature line
    source = textwrap.dedent(inspect.getsource(script_fn).split("\n", 1)[1])
    with NamedTemporaryFile() as file:
        file.write(source.encode())
        file.flush()
        yield file.name
