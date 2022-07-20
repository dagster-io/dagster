from contextlib import contextmanager
from io import IOBase
from typing import IO, Iterator, List, Optional, Sequence, TypeVar, Union, overload
import os

T = TypeVar("T")


def discover_repo_root() -> str:
    cdir = os.path.dirname(__file__)
    while True:
        if os.path.exists(os.path.join(cdir, ".git")):
            return os.path.abspath(cdir)
        elif os.path.dirname(cdir) == cdir:  # filesystem root
            raise Exception("Could not find git repository root")
        else:
            cdir = os.path.dirname(cdir)


@contextmanager
def in_cwd(path: str) -> Iterator[None]:
    origin = os.getcwd()
    try:
        os.chdir(path)
        yield
    finally:
        os.chdir(origin)


def not_none(value: Optional[T], additional_message: Optional[str] = None) -> T:
    if value is None:
        raise ValueError(f"Expected non-None value: {additional_message}")
    return value


@overload
def index_with_default(lst: Sequence[object], k: object, default: None = ...) -> Optional[int]:
    ...


@overload
def index_with_default(lst: Sequence[object], k: object, default: int = ...) -> int:
    ...


def index_with_default(
    lst: Sequence[object], k: object, default: Optional[int] = None
) -> Optional[int]:
    try:
        return lst.index(k)
    except ValueError:
        return default


def read_file(file: Union[str, IO[str]]) -> str:
    if isinstance(file, str):
        with open(file, "r", encoding="utf-8") as f:
            return f.read()
    else:
        return file.read()


def write_file(file: Union[str, IO[str]], content: Union[str, Sequence[str]]):
    content = "\n".join(content) if not isinstance(content, str) else content
    if isinstance(file, str):
        with open(file, "w", encoding="utf-8") as f:
            f.write(content)
    else:
        file.write(content)
