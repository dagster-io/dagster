import inspect
import textwrap
from collections.abc import Iterator
from contextlib import contextmanager
from tempfile import NamedTemporaryFile
from typing import Any, Callable


@contextmanager
def temp_script(script_fn: Callable[[], Any]) -> Iterator[str]:
    # drop the signature line
    source = textwrap.dedent(inspect.getsource(script_fn).split("\n", 1)[1])
    with NamedTemporaryFile() as file:
        file.write(source.encode())
        file.flush()
        yield file.name
