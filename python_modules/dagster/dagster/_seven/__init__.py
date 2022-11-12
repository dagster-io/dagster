"""Internal py2/3 compatibility library. A little more than six."""
import datetime
import inspect
import os
import shlex
import signal
import sys
import tempfile
import threading
import time
from contextlib import contextmanager
from datetime import timezone
from types import ModuleType
from typing import Any, Callable, List, Sequence, Type

import pendulum
from typing_extensions import TypeGuard

from .compat.pendulum import PendulumDateTime
from .json import JSONDecodeError, dump, dumps
from .temp_dir import get_system_temp_directory

IS_WINDOWS = os.name == "nt"

funcsigs = inspect

IS_WINDOWS = os.name == "nt"

# TODO implement a generic import by name -- see https://stackoverflow.com/questions/301134/how-to-import-a-module-given-its-name

# https://stackoverflow.com/a/67692/324449
def import_module_from_path(module_name: str, path_to_file: str) -> ModuleType:
    import importlib.util

    spec = importlib.util.spec_from_file_location(module_name, path_to_file)
    if spec is None:
        raise Exception(
            "Can not import module {module_name} from path {path_to_file}, unable to load spec.".format(
                module_name=module_name, path_to_file=path_to_file
            )
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


def is_ascii(str_):
    if sys.version_info.major == 3 and sys.version_info.minor < 7:
        try:
            str_.encode("ascii")
            return True
        except UnicodeEncodeError:
            return False
    else:
        return str_.isascii()


time_fn = time.perf_counter


def get_arg_names(callable_: Callable[..., Any]) -> Sequence[str]:
    return [
        parameter.name
        for parameter in inspect.signature(callable_).parameters.values()
        if parameter.kind == inspect.Parameter.POSITIONAL_OR_KEYWORD
    ]


def wait_for_process(process, timeout=30):
    # Using Popen.communicate instead of Popen.wait since the latter
    # can deadlock, see https://docs.python.org/3/library/subprocess.html#subprocess.Popen.wait
    if not timeout:
        process.communicate()
    elif sys.version_info.major >= 3:
        process.communicate(timeout=timeout)
    else:
        timed_out_event = threading.Event()

        def _wait_timeout():
            timed_out_event.set()
            process.kill()

        timer = threading.Timer(timeout, _wait_timeout)
        try:
            timer.start()
            process.wait()
        finally:
            timer.cancel()

        if timed_out_event.is_set():
            raise Exception("Timed out waiting for process to finish")


def kill_process(process):
    import multiprocessing

    if not isinstance(process, multiprocessing.Process):
        raise Exception("invalid process argument passed to kill_process")

    if sys.version_info >= (3, 7):
        # Kill added in 3.7
        process.kill()
    else:
        process.terminate()


# https://stackoverflow.com/a/58437485/324449
def is_module_available(module_name: str) -> bool:
    # python 3.4 and above
    import importlib.util

    loader = importlib.util.find_spec(module_name)

    return loader is not None


def builtin_print() -> str:
    return "builtins.print"


def get_current_datetime_in_utc() -> Any:
    return pendulum.now("UTC")


def get_timestamp_from_utc_datetime(utc_datetime):

    if isinstance(utc_datetime, PendulumDateTime):
        return utc_datetime.timestamp()

    if utc_datetime.tzinfo != timezone.utc:
        raise Exception("Must pass in a UTC timezone to compute UNIX timestamp")

    return utc_datetime.timestamp()


def is_lambda(target: object) -> TypeGuard[Callable[..., Any]]:
    return callable(target) and getattr(target, "__name__", None) == "<lambda>"


def is_function_or_decorator_instance_of(
    target: object, kls: Type[Any]
) -> TypeGuard[Callable[..., Any]]:
    return inspect.isfunction(target) or (isinstance(target, kls) and hasattr(target, "__name__"))


def qualname_differs(target: object) -> bool:
    return hasattr(target, "__qualname__") and getattr(target, "__qualname__") != getattr(
        target, "__name__"
    )


def xplat_shlex_split(s: str) -> List[str]:
    if IS_WINDOWS:
        return shlex.split(s, posix=False)

    return shlex.split(s)


def get_import_error_message(import_error: ImportError) -> str:
    return import_error.msg


# Stand-in for contextlib.nullcontext, but available in python 3.6
@contextmanager
def nullcontext():
    yield


def is_subclass(child_type: Type[Any], parent_type: Type[Any]):
    """Due to some pathological interactions betwen bugs in the Python typing library
    (https://github.com/python/cpython/issues/88459 and
    https://github.com/python/cpython/issues/89010), some types (list[str] in Python 3.9, for
    example) pass inspect.isclass check above but then raise an exception if issubclass is called
    with the same class. This function provides a workaround for that issue."""

    if not inspect.isclass(child_type):
        return False

    try:
        return issubclass(child_type, parent_type)
    except TypeError:
        return False
