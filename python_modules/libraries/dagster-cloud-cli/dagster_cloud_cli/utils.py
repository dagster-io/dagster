import collections
import contextlib
import functools
import inspect
import math
import os
import socket
from typing import Any

import typer
from typer.models import OptionInfo

from dagster_cloud_cli import ui

DEFAULT_PYTHON_VERSION = "3.11"


def create_stub_app(package_name: str) -> typer.Typer:
    return typer.Typer(
        help=f"This command is not available unless you install the {package_name} package.",
        hidden=True,
    )


def create_stub_command(package_name: str):
    def fn():
        ui.print(f"This command is not available unless you install the {package_name} package.")

    return fn


# Same as dagster._utils.find_free_port
def find_free_port():
    with contextlib.closing(socket.socket(socket.AF_INET, socket.SOCK_STREAM)) as s:
        s.bind(("", 0))
        s.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        return s.getsockname()[1]


def with_added_params(
    signature: inspect.Signature, to_add: dict[str, inspect.Parameter]
) -> inspect.Signature:
    """Returns a new signature based on the provided one, with the provided parameters added."""
    params = collections.OrderedDict(signature.parameters)
    for k, v in to_add.items():
        params[k] = v
    return signature.replace(parameters=list(params.values()))


def without_params(signature: inspect.Signature, to_remove: list[str]) -> inspect.Signature:
    """Returns a new signature based on the provided one with the given parameters removed by name.
    Does nothing if the parameter is not found.
    """
    params = collections.OrderedDict(signature.parameters)
    for r in to_remove:
        if r in params:
            del params[r]
    return signature.replace(parameters=list(params.values()))


def add_options(options: dict[str, tuple[Any, OptionInfo]]):
    """Decorator to add Options to a particular command."""

    def decorator(to_wrap):
        # Ensure that the function signature has the correct typer.Option defaults,
        # so that every command need not specify them

        # Remove kwargs, since Typer doesn't know how to handle it
        to_wrap_sig = inspect.signature(to_wrap)
        has_kwargs = "kwargs" in to_wrap_sig.parameters
        sig = without_params(to_wrap_sig, ["kwargs"])
        sig = with_added_params(
            sig,
            {
                name: inspect.Parameter(
                    name,
                    inspect.Parameter.POSITIONAL_OR_KEYWORD,
                    annotation=_type,
                    default=default,
                )
                for name, (_type, default) in options.items()
            },
        )

        @functools.wraps(to_wrap)
        def wrap_function(*args, **kwargs):
            modified_kwargs = kwargs
            if not has_kwargs and not hasattr(to_wrap, "modified_options"):
                modified_kwargs: dict[Any, Any] = {
                    k: v for k, v in kwargs.items() if k in to_wrap_sig.parameters
                }
            return to_wrap(*args, **modified_kwargs)

        wrap_function.__signature__ = sig  # pyright: ignore[reportAttributeAccessIssue]
        wrap_function.modified_options = True  # pyright: ignore[reportAttributeAccessIssue]
        return wrap_function

    return decorator


def get_file_size(path) -> str:
    size = os.path.getsize(path)
    if size == 0:
        return "0 bytes"
    units = ["bytes", "KB", "MB", "GB"]
    magnitude = math.floor(math.log(size, 1024))
    magnitude = min([len(units) - 1, magnitude])

    unit = units[magnitude]
    value = size // (1024**magnitude)
    return f"{value} {unit}"
