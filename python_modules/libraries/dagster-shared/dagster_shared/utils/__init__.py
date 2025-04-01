import contextlib
import socket
from typing import TypeVar

T = TypeVar("T")


def find_free_port() -> int:
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
