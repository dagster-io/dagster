"""Internal py2/3 compatibility library. A little more than six."""

import datetime
import inspect
import multiprocessing
import os
import shlex
import signal
import sys
import tempfile
import threading
import time
from types import MethodType

from .json import JSONDecodeError, dump, dumps
from .temp_dir import get_system_temp_directory

IS_WINDOWS = os.name == "nt"

if hasattr(inspect, "signature"):
    funcsigs = inspect
else:
    import funcsigs

# pylint: disable=no-name-in-module,import-error,no-member
if sys.version_info < (3, 0):
    # Python 2 tempfile doesn't have tempfile.TemporaryDirectory
    import backports.tempfile

    TemporaryDirectory = backports.tempfile.TemporaryDirectory

else:
    TemporaryDirectory = tempfile.TemporaryDirectory

try:
    # pylint:disable=redefined-builtin,self-assigning-variable
    FileNotFoundError = FileNotFoundError
except NameError:
    FileNotFoundError = IOError

try:
    from functools import lru_cache
except ImportError:
    from functools32 import lru_cache

try:
    # pylint:disable=redefined-builtin,self-assigning-variable
    ModuleNotFoundError = ModuleNotFoundError
except NameError:
    ModuleNotFoundError = ImportError

try:
    import _thread as thread
except ImportError:
    import thread

try:
    from urllib.parse import urljoin, urlparse, urlunparse, quote_plus
except ImportError:
    from urlparse import urljoin, urlparse, urlunparse
    from urllib import quote_plus

try:
    from itertools import zip_longest
except ImportError:
    from itertools import izip_longest as zip_longest

if sys.version_info > (3,):
    from pathlib import Path  # pylint: disable=import-error
else:
    from pathlib2 import Path  # pylint: disable=import-error

if sys.version_info > (3,):
    from contextlib import ExitStack  # pylint: disable=import-error
else:
    from contextlib2 import ExitStack  # pylint: disable=import-error

if sys.version_info > (3,):
    from threading import Event as ThreadingEventType  # pylint: disable=import-error
else:
    from threading import _Event as ThreadingEventType  # pylint: disable=import-error

# Set execution method to spawn, to avoid fork and to have same behavior between platforms.
# Older versions are stuck with whatever is the default on their platform (fork on
# Unix-like and spawn on windows)
#
# https://docs.python.org/3/library/multiprocessing.html#multiprocessing.get_context
if hasattr(multiprocessing, "get_context"):
    multiprocessing = multiprocessing.get_context("spawn")


IS_WINDOWS = os.name == "nt"

# TODO implement a generic import by name -- see https://stackoverflow.com/questions/301134/how-to-import-a-module-given-its-name

# https://stackoverflow.com/a/67692/324449
def import_module_from_path(module_name, path_to_file):
    version = sys.version_info
    if version.major >= 3 and version.minor >= 5:
        import importlib.util

        spec = importlib.util.spec_from_file_location(module_name, path_to_file)
        if spec is None:
            raise Exception(
                "Can not import module {module_name} from path {path_to_file}, unable to load spec.".format(
                    module_name=module_name, path_to_file=path_to_file
                )
            )
        if sys.modules.get(spec.name) and sys.modules[spec.name].__file__ == os.path.abspath(
            spec.origin
        ):
            module = sys.modules[spec.name]
        else:
            module = importlib.util.module_from_spec(spec)
            sys.modules[spec.name] = module
            spec.loader.exec_module(module)
    elif version.major >= 3 and version.minor >= 3:
        from importlib.machinery import SourceFileLoader

        # pylint:disable=deprecated-method, no-value-for-parameter
        module = SourceFileLoader(module_name, path_to_file).load_module()
    else:
        from imp import load_source

        module = load_source(module_name, path_to_file)

    return module


def is_ascii(str_):
    if sys.version_info.major < 3:
        try:
            str_.decode("ascii")
            return True
        except UnicodeEncodeError:
            return False
    elif sys.version_info.major == 3 and sys.version_info.minor < 7:
        try:
            str_.encode("ascii")
            return True
        except UnicodeEncodeError:
            return False
    else:
        return str_.isascii()


if sys.version_info.major >= 3 and sys.version_info.minor >= 3:
    time_fn = time.perf_counter
elif IS_WINDOWS:
    time_fn = time.clock
else:
    time_fn = time.time

try:
    from unittest import mock
except ImportError:
    # Because this dependency is not encoded setup.py deliberately
    # (we do not want to override or conflict with our users mocks)
    # we never fail when importing this.

    # This will only be used within *our* test environment of which
    # we have total control
    try:
        import mock
    except ImportError:
        pass


def get_args(callable_):
    if sys.version_info.major >= 3:
        return [
            parameter.name
            for parameter in inspect.signature(callable_).parameters.values()
            if parameter.kind == inspect.Parameter.POSITIONAL_OR_KEYWORD
        ]
    else:
        if inspect.isclass(callable_):
            if issubclass(callable_, tuple):
                arg_spec = inspect.getargspec(  # pylint: disable=deprecated-method
                    callable_.__new__
                )
            else:
                arg_spec = inspect.getargspec(  # pylint: disable=deprecated-method
                    callable_.__init__
                )
        else:
            arg_spec = inspect.getargspec(callable_)  # pylint: disable=deprecated-method
        return arg_spec.args


def wait_for_process(process, timeout=None):
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


# https://stackoverflow.com/a/58437485/324449
def is_module_available(module_name):
    if sys.version_info <= (3, 3):
        # python 3.3 and below
        import pkgutil

        loader = pkgutil.find_loader(module_name)
    elif sys.version_info >= (3, 4):
        # python 3.4 and above
        import importlib

        loader = importlib.util.find_spec(module_name)

    return loader is not None


def builtin_print():
    if sys.version_info.major >= 3:
        return "builtins.print"

    else:
        return "sys.stdout"


def print_single_line_str(single_line_str):
    if sys.version_info.major >= 3:
        return [
            mock.call(single_line_str),
        ]
    else:
        return [
            mock.call.write(single_line_str),
            mock.call.write("\n"),
        ]


def get_current_datetime_in_utc():
    tz = None
    if sys.version_info.major >= 3 and sys.version_info.minor >= 2:
        from datetime import timezone

        tz = timezone.utc
    else:
        import pytz

        tz = pytz.utc

    return datetime.datetime.now(tz=tz)


def is_lambda(target):
    return callable(target) and (hasattr(target, "__name__") and target.__name__ == "<lambda>")


def is_function_or_decorator_instance_of(target, kls):
    return inspect.isfunction(target) or (isinstance(target, kls) and hasattr(target, "__name__"))


def qualname_differs(target):
    return hasattr(target, "__qualname__") and (target.__qualname__ != target.__name__)


def xplat_shlex_split(s):
    if IS_WINDOWS:
        return shlex.split(s, posix=False)

    return shlex.split(s)
