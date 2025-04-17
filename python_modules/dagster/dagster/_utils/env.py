import os
import sys
from collections.abc import Iterator, Mapping
from contextlib import contextmanager
from pathlib import Path
from typing import Union


@contextmanager
def environ(env: Mapping[str, str]) -> Iterator[None]:
    """Temporarily set environment variables inside the context manager and
    fully restore previous environment afterwards.
    """
    previous_values = {key: os.getenv(key) for key in env}
    for key, value in env.items():
        if value is None:
            if key in os.environ:
                del os.environ[key]
        else:
            os.environ[key] = value
    try:
        yield
    finally:
        for key, value in previous_values.items():
            if value is None:
                if key in os.environ:
                    del os.environ[key]
            else:
                os.environ[key] = value


def using_dagster_dev() -> bool:
    return bool(os.getenv("DAGSTER_IS_DEV_CLI"))


def use_verbose() -> bool:
    return bool(os.getenv("DAGSTER_verbose", "1"))


@contextmanager
def activate_venv(venv_path: Union[str, Path]) -> Iterator[None]:
    """Simulated activation of the passed in virtual environment for the current process."""
    venv_path = (Path(venv_path) if isinstance(venv_path, str) else venv_path).absolute()
    with environ(
        {
            "VIRTUAL_ENV": str(venv_path),
            "PATH": os.pathsep.join(
                [
                    str(venv_path / ("Scripts" if sys.platform == "win32" else "bin")),
                    os.getenv("PATH", ""),
                ]
            ),
        }
    ):
        yield
