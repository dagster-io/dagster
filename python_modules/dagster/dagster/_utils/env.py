import os
from collections.abc import Iterator, Mapping
from contextlib import contextmanager


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
