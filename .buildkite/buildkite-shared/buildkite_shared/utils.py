import os
from collections.abc import Iterator
from contextlib import contextmanager
from pathlib import Path


@contextmanager
def pushd(path: Path) -> Iterator[None]:
    prev_dir = os.getcwd()
    os.chdir(path)
    try:
        yield
    finally:
        os.chdir(prev_dir)
