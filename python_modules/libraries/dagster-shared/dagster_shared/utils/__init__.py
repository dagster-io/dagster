import contextlib
import os
import random
import socket
from typing import TypeVar

T = TypeVar("T")


def _find_free_port_in_range(start: int, end: int) -> int:
    ports_to_try = list(range(start, end + 1))
    with contextlib.closing(socket.socket(socket.AF_INET, socket.SOCK_STREAM)) as s:
        random.shuffle(ports_to_try)
        for port in ports_to_try:
            try:
                s.bind(("", port))
                s.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
                return port
            except OSError:
                continue

        raise Exception(f"No free ports found in range {start}-{end}")


def find_free_port() -> int:
    port_range = os.getenv("DAGSTER_PORT_RANGE")
    if port_range:
        split_range = port_range.split("-")
        if len(split_range) != 2:
            raise Exception("DAGSTER_PORT_RANGE must be of the form 'start-end'")
        return _find_free_port_in_range(int(split_range[0]), int(split_range[1]))

    with contextlib.closing(socket.socket(socket.AF_INET, socket.SOCK_STREAM)) as s:
        s.bind(("", 0))
        s.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        return s.getsockname()[1]


def remove_none_recursively(obj: T) -> T:
    """Remove none values from a dict. This can be used to support comparing provided config vs.
    config we retrive from kubernetes, which returns all fields, even those which have no value
    configured.
    """
    if isinstance(obj, (list, tuple, set)):
        return type(obj)(remove_none_recursively(x) for x in obj if x is not None)
    elif isinstance(obj, dict):
        return type(obj)(
            (remove_none_recursively(k), remove_none_recursively(v))
            for k, v in obj.items()
            if k is not None and v is not None
        )
    else:
        return obj
