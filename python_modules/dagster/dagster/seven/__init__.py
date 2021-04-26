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
from contextlib import contextmanager
from datetime import timezone
from types import MethodType

import pendulum
import pkg_resources

from .json import JSONDecodeError, dump, dumps
from .temp_dir import get_system_temp_directory

IS_WINDOWS = os.name == "nt"

funcsigs = inspect

multiprocessing = multiprocessing.get_context("spawn")  # type: ignore[assignment]

IS_WINDOWS = os.name == "nt"

# TODO implement a generic import by name -- see https://stackoverflow.com/questions/301134/how-to-import-a-module-given-its-name

# https://stackoverflow.com/a/67692/324449
def import_module_from_path(module_name, path_to_file):
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


def get_args(callable_):
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
    if not isinstance(process, multiprocessing.Process):
        raise Exception("invalid process argument passed to kill_process")

    if sys.version_info >= (3, 7):
        # Kill added in 3.7
        process.kill()
    else:
        process.terminate()


# https://stackoverflow.com/a/58437485/324449
def is_module_available(module_name):
    # python 3.4 and above
    import importlib

    loader = importlib.util.find_spec(module_name)

    return loader is not None


def builtin_print():
    return "builtins.print"


def get_current_datetime_in_utc():
    return pendulum.now("UTC")


def get_timestamp_from_utc_datetime(utc_datetime):

    if isinstance(utc_datetime, PendulumDateTime):
        return utc_datetime.timestamp()

    if utc_datetime.tzinfo != timezone.utc:
        raise Exception("Must pass in a UTC timezone to compute UNIX timestamp")

    return utc_datetime.timestamp()


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


def get_import_error_message(import_error):
    return import_error.msg


# Stand-in for contextlib.nullcontext, but available in python 3.6
@contextmanager
def nullcontext():
    yield


_IS_PENDULUM_2 = pkg_resources.get_distribution("pendulum").version.split(".")[0] == "2"


@contextmanager
def mock_pendulum_timezone(override_timezone):
    if _IS_PENDULUM_2:
        with pendulum.tz.test_local_timezone(  # pylint: disable=no-member
            pendulum.tz.timezone(override_timezone)  # pylint: disable=no-member
        ):

            yield
    else:
        with pendulum.tz.LocalTimezone.test(  # pylint: disable=no-member
            pendulum.Timezone.load(override_timezone)  # pylint: disable=no-member
        ):

            yield


def create_pendulum_time(year, month, day, *args, **kwargs):
    return (
        pendulum.datetime(  # pylint: disable=no-member, pendulum-create
            year, month, day, *args, **kwargs
        )
        if _IS_PENDULUM_2
        else pendulum.create(  # pylint: disable=no-member, pendulum-create
            year, month, day, *args, **kwargs
        )
    )


PendulumDateTime = (
    pendulum.DateTime if _IS_PENDULUM_2 else pendulum.Pendulum  # pylint: disable=no-member
)

# Workaround for issues with .in_tz() in pendulum:
# https://github.com/sdispater/pendulum/issues/535
def to_timezone(dt, tz):
    from dagster import check

    check.inst_param(dt, "dt", PendulumDateTime)
    return pendulum.from_timestamp(dt.timestamp(), tz=tz)
