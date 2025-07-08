"""Internal py2/3 compatibility library. A little more than six."""

import importlib.util
import inspect
import os
import pkgutil
import shlex
import sys
import time
from collections.abc import Sequence
from importlib.machinery import ModuleSpec
from pathlib import Path
from types import ModuleType
from typing import Any, Callable, List, Optional, Type, Union  # noqa: F401, UP035

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
IS_PYTHON_3_13 = (sys.version_info[0], sys.version_info[1]) == (3, 13)

# TODO implement a generic import by name -- see https://stackoverflow.com/questions/301134/how-to-import-a-module-given-its-name


# https://stackoverflow.com/a/67692/324449
def import_module_from_path(module_name: str, path_to_file: Union[str, Path]) -> ModuleType:
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


def resolve_module_pattern(pattern: str) -> list[str]:
    """Find all modules that match the given pattern segments.

    Note that this will only return modules that have been verified to exist using
    importlib.util.find_spec. This means that a pure literal pattern like "foo.bar" will
    return an empty list if the module does not exist.

    Args:
        pattern_segments: List of pattern segments, where * matches any segment name.

    Returns:
        List of matching module names.
    """
    pattern_segments = pattern.split(".")
    return _gather_modules([], pattern_segments)


def _gather_modules(current_segments: list[str], remaining_pattern: list[str]) -> list[str]:
    if not remaining_pattern:
        # We've matched the full pattern, return the current module path
        module_name = ".".join(current_segments)
        # Verify the module actually exists and can be imported
        if _get_module_spec(module_name) is not None:
            return [module_name]
        else:
            return []

    current_pattern = remaining_pattern[0]
    rest_pattern = remaining_pattern[1:]

    # Wildcard
    if current_pattern == "*":
        if len(current_segments) == 0:  # top-level wildcard
            current_module_path = None
        else:
            current_module_name = ".".join(current_segments)
            current_module_spec = _get_module_spec(current_module_name)
            if (
                current_module_spec is None
                or current_module_spec.submodule_search_locations is None
            ):
                return []
            else:
                current_module_path = current_module_spec.submodule_search_locations

        # Explore all top-level packages
        matches = []
        for _, name, _ in pkgutil.iter_modules(current_module_path):
            matches.extend(_gather_modules([*current_segments, name], rest_pattern))
        return matches

    # Literal
    else:
        # Literal segment - add it and continue
        return _gather_modules([*current_segments, current_pattern], rest_pattern)


def _get_module_spec(module_name: str) -> Optional[ModuleSpec]:
    try:
        return importlib.util.find_spec(module_name)

    # ModuleNotFoundError gets thrown if you try to find a spec where one of the parent modules does
    # not exist, e.g. "foo.bar.baz" when "foo" does not exist.
    except ModuleNotFoundError:
        return None


def match_module_pattern(module_name: str, pattern: str) -> bool:
    """Check if a module name matches a given pattern."""
    pattern_segments = pattern.split(".")
    module_segments = module_name.split(".")

    if len(pattern_segments) != len(module_segments):
        return False

    for pattern_segment, module_segment in zip(pattern_segments, module_segments):
        if pattern_segment != "*" and pattern_segment != module_segment:
            return False

    return True


def is_valid_module_pattern(pattern: str) -> bool:
    """Check if a module pattern is valid."""
    if not pattern:
        return False

    for segment in pattern.split("."):
        if not (segment.isidentifier() or segment == "*"):
            return False

    return True


def load_module_object(module_name: str, attr: str) -> object:
    """Loads a top-level attribute from a module.

    Args:
        module_name: The name of the module to load the attribute from.
        attr: The name of the attribute to load.

    Returns:
        The attribute value.

    Raises:
        DagsterUnresolvableSymbolError: If the module or attribute is not found.
    """
    from dagster_shared.error import DagsterUnresolvableSymbolError

    try:
        module = importlib.import_module(module_name)
        if not hasattr(module, attr):
            raise DagsterUnresolvableSymbolError(
                f"Module `{module_name}` has no attribute `{attr}`."
            )
        return getattr(module, attr)
    except ModuleNotFoundError as e:
        raise DagsterUnresolvableSymbolError(f"Module `{module_name}` not found.") from e
    except ImportError as e:
        raise DagsterUnresolvableSymbolError(f"Error loading module `{module_name}`.") from e
