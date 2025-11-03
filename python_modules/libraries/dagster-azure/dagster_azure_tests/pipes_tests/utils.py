import inspect
import shutil
import textwrap
from collections.abc import Iterator
from contextlib import contextmanager
from pathlib import Path
from tempfile import NamedTemporaryFile
from typing import Any, Callable

_PYTHON_EXECUTABLE = shutil.which("python") or "python"


@contextmanager
def temp_script(script_fn: Callable[[], Any], mock_blob_storage_class: Any) -> Iterator[str]:
    mock_blob_storage_source = Path(inspect.getfile(mock_blob_storage_class)).read_text()
    # drop the signature line
    function_source = textwrap.dedent(inspect.getsource(script_fn).split("\n", 1)[1])

    with NamedTemporaryFile() as file:
        file.write(mock_blob_storage_source.encode())
        file.write(b"\n\n")
        file.write(function_source.encode())
        file.flush()
        yield file.name
