"""Internal py2/3 compatibility library. A little more than six."""

import inspect
import os
import shlex
import sys
import time
from collections.abc import Sequence
from types import ModuleType
from typing import Any, Callable, List, Type  # noqa: F401, UP035

from typing_extensions import TypeGuard

import dagster_shared.seven.json as json  # noqa: F401
from dagster_shared.seven.json import (
    JSONDecodeError as JSONDecodeError,
    dump as dump,
    dumps as dumps,
)
from dagster_shared.seven.temp_dir import get_system_temp_directory as get_system_temp_directory

IS_WINDOWS = os.name == "nt"
IS_PYTHON_3_12 = (sys.version_info[0], sys.version_info[1]) == (3, 12)

# TODO implement a generic import by name -- see https://stackoverflow.com/questions/301134/how-to-import-a-module-given-its-name


# https://stackoverflow.com/a/67692/324449
def import_module_from_path(module_name: str, path_to_file: str) -> ModuleType:
    import importlib.util

    spec = importlib.util.spec_from_file_location(module_name, path_to_file)
    if spec is None:
        raise Exception(
            f"Can not import module {module_name} from path {path_to_file}, unable to load spec."
        )

    if sys.modules.get(spec.name) and spec.origin:
        f = sys.modules[spec.name].__file__
        # __file__ can be relative depending on current working directory
        if f and os.path.abspath(f) == os.path.abspath(spec.origin):
            return sys.modules[spec.name]

    module = importlib.util.module_from_spec(spec)
    sys.modules[spec.name] = module
    assert spec.loader
    spec.loader.exec_module(module)
    return module


def import_uncached_module_from_path(module_name: str, path_to_file: str) -> ModuleType:
    import importlib.util

    spec = importlib.util.spec_from_file_location(module_name, path_to_file)
    if spec is None:
        raise Exception(
            f"Can not import module {module_name} from path {path_to_file}, unable to load spec."
        )

    module = importlib.util.module_from_spec(spec)
    assert spec.loader
    spec.loader.exec_module(module)
    return module


time_fn = time.perf_counter


def get_arg_names(callable_: Callable[..., Any]) -> Sequence[str]:
    return [
        parameter.name
        for parameter in inspect.signature(callable_).parameters.values()
        if parameter.kind == inspect.Parameter.POSITIONAL_OR_KEYWORD
    ]


# https://stackoverflow.com/a/58437485/324449
def is_module_available(module_name: str) -> bool:
    # python 3.4 and above
    import importlib.util

    loader = importlib.util.find_spec(module_name)

    return loader is not None


def is_lambda(target: object) -> TypeGuard[Callable[..., Any]]:
    return callable(target) and getattr(target, "__name__", None) == "<lambda>"


def is_function_or_decorator_instance_of(
    target: object, kls: type[Any]
) -> TypeGuard[Callable[..., Any]]:
    return inspect.isfunction(target) or (isinstance(target, kls) and hasattr(target, "__name__"))


def qualname_differs(target: object) -> bool:
    return hasattr(target, "__qualname__") and getattr(target, "__qualname__") != getattr(
        target, "__name__"
    )


def xplat_shlex_split(s: str) -> list[str]:
    if IS_WINDOWS:
        return shlex.split(s, posix=False)

    return shlex.split(s)


def get_import_error_message(import_error: ImportError) -> str:
    return import_error.msg


def is_subclass(child_type: type[Any], parent_type: type[Any]):
    """Due to some pathological interactions betwen bugs in the Python typing library
    (https://github.com/python/cpython/issues/88459 and
    https://github.com/python/cpython/issues/89010), some types (list[str] in Python 3.9, for
    example) pass inspect.isclass check above but then raise an exception if issubclass is called
    with the same class. This function provides a workaround for that issue.
    """
    if not inspect.isclass(child_type):
        return False

    try:
        return issubclass(child_type, parent_type)
    except TypeError:
        return False
