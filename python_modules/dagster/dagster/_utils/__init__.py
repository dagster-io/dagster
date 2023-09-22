import _thread as thread
import contextlib
import contextvars
import datetime
import errno
import functools
import inspect
import multiprocessing
import os
import re
import signal
import socket
import subprocess
import sys
import tempfile
import threading
import time
from collections import OrderedDict
from datetime import timezone
from enum import Enum
from signal import Signals
from typing import (
    TYPE_CHECKING,
    AbstractSet,
    Any,
    Callable,
    ContextManager,
    Dict,
    Generator,
    Generic,
    Hashable,
    Iterator,
    List,
    Mapping,
    NamedTuple,
    Optional,
    Sequence,
    Set,
    Tuple,
    Type,
    TypeVar,
    Union,
    cast,
    overload,
)

import packaging.version
from typing_extensions import Literal, TypeAlias, TypeGuard

import dagster._check as check
import dagster._seven as seven

from .internal_init import IHasInternalInit as IHasInternalInit

if sys.version_info > (3,):
    from pathlib import Path
else:
    from pathlib2 import Path

if TYPE_CHECKING:
    from dagster._core.definitions.definitions_class import Definitions
    from dagster._core.definitions.repository_definition.repository_definition import (
        RepositoryDefinition,
    )
    from dagster._core.events import DagsterEvent

K = TypeVar("K")
T = TypeVar("T")
U = TypeVar("U")
V = TypeVar("V")

EPOCH = datetime.datetime.utcfromtimestamp(0)

PICKLE_PROTOCOL = 4


DEFAULT_WORKSPACE_YAML_FILENAME = "workspace.yaml"

PrintFn: TypeAlias = Callable[[Any], None]

SingleInstigatorDebugCrashFlags: TypeAlias = Mapping[str, int]
DebugCrashFlags: TypeAlias = Mapping[str, SingleInstigatorDebugCrashFlags]


# Use this to get the "library version" (pre-1.0 version) from the "core version" (post 1.0
# version). 16 is from the 0.16.0 that library versions stayed on when core went to 1.0.0.
def library_version_from_core_version(core_version: str) -> str:
    parsed_version = parse_package_version(core_version)

    release = parsed_version.release
    if release[0] >= 1:
        library_version = ".".join(["0", str(16 + release[1]), str(release[2])])

        if parsed_version.is_prerelease:
            library_version = library_version + "".join(
                [str(pre) for pre in check.not_none(parsed_version.pre)]
            )

        if parsed_version.is_postrelease:
            library_version = library_version + "post" + str(parsed_version.post)

        return library_version
    else:
        return core_version


def parse_package_version(version_str: str) -> packaging.version.Version:
    parsed_version = packaging.version.parse(version_str)
    assert isinstance(parsed_version, packaging.version.Version)
    return parsed_version


def convert_dagster_submodule_name(name: str, mode: Literal["private", "public"]) -> str:
    """This function was introduced when all Dagster submodules were marked private by
    underscore-prefixing the root submodules (e.g. `dagster._core`). The function provides
    backcompatibility by converting modules between the old and new (i.e. public and private) forms.
    This is needed when reading older data or communicating with older versions of Dagster.
    """
    if mode == "private":
        return re.sub(r"^dagster\.([^_])", r"dagster._\1", name)
    elif mode == "public":
        return re.sub(r"^dagster._", "dagster.", name)
    else:
        check.failed("`mode` must be 'private' or 'public'")


def file_relative_path(dunderfile: str, relative_path: str) -> str:
    """Get a path relative to the currently executing Python file.

    This function is useful when one needs to load a file that is relative to the position of
    the current file. (Such as when you encode a configuration file path in source file and want
    in runnable in any current working directory)

    Args:
        dunderfile (str): Should always be ``__file__``.
        relative_path (str): Path to get relative to the currently executing file.

    **Examples**:

    .. code-block:: python

        file_relative_path(__file__, 'path/relative/to/file')

    """
    check.str_param(dunderfile, "dunderfile")
    check.str_param(relative_path, "relative_path")

    return os.path.join(os.path.dirname(dunderfile), relative_path)


def script_relative_path(file_path: str) -> str:
    """Useful for testing with local files. Use a path relative to where the
    test resides and this function will return the absolute path
    of that file. Otherwise it will be relative to script that
    ran the test.

    Note: this is function is very, very expensive (on the order of 1
    millisecond per invocation) so this should only be used in performance
    insensitive contexts. Prefer file_relative_path for anything with
    performance constraints.

    """
    # from http://bit.ly/2snyC6s

    check.str_param(file_path, "file_path")
    scriptdir = inspect.stack()[1][1]
    return os.path.abspath(os.path.join(os.path.dirname(os.path.abspath(scriptdir)), file_path))


# Adapted from https://github.com/okunishinishi/python-stringcase/blob/master/stringcase.py
def camelcase(string: str) -> str:
    check.str_param(string, "string")

    string = re.sub(r"^[\-_\.]", "", str(string))
    if not string:
        return string
    return str(string[0]).upper() + re.sub(
        r"[\-_\.\s]([a-z])", lambda matched: str(matched.group(1)).upper(), string[1:]
    )


def ensure_single_item(ddict: Mapping[T, U]) -> Tuple[T, U]:
    check.mapping_param(ddict, "ddict")
    check.param_invariant(len(ddict) == 1, "ddict", "Expected dict with single item")
    return next(iter(ddict.items()))


@contextlib.contextmanager
def pushd(path: str) -> Iterator[str]:
    old_cwd = os.getcwd()
    os.chdir(path)
    try:
        yield path
    finally:
        os.chdir(old_cwd)


def safe_isfile(path: str) -> bool:
    """Backport of Python 3.8 os.path.isfile behavior.

    This is intended to backport https://docs.python.org/dev/whatsnew/3.8.html#os-path. I'm not
    sure that there are other ways to provoke this behavior on Unix other than the null byte,
    but there are certainly other ways to do it on Windows. Afaict, we won't mask other
    ValueErrors, and the behavior in the status quo ante is rough because we risk throwing an
    unexpected, uncaught ValueError from very deep in our logic.
    """
    try:
        return os.path.isfile(path)
    except ValueError:
        return False


def mkdir_p(path: str) -> str:
    try:
        os.makedirs(path)
        return path
    except OSError as exc:  # Python >2.5
        if exc.errno == errno.EEXIST and os.path.isdir(path):
            return path
        else:
            raise


def hash_collection(
    collection: Union[
        Mapping[Hashable, Any], Sequence[Any], AbstractSet[Any], Tuple[Any, ...], NamedTuple
    ]
) -> int:
    """Hash a mutable collection or immutable collection containing mutable elements.

    This is useful for hashing Dagster-specific NamedTuples that contain mutable lists or dicts.
    The default NamedTuple __hash__ function assumes the contents of the NamedTuple are themselves
    hashable, and will throw an error if they are not. This can occur when trying to e.g. compute a
    cache key for the tuple for use with `lru_cache`.

    This alternative implementation will recursively process collection elements to convert basic
    lists and dicts to tuples prior to hashing. It is recommended to cache the result:

    Example:
        .. code-block:: python

            def __hash__(self):
                if not hasattr(self, '_hash'):
                    self._hash = hash_named_tuple(self)
                return self._hash
    """
    assert isinstance(
        collection, (list, dict, set, tuple)
    ), f"Cannot hash collection of type {type(collection)}"
    return hash(make_hashable(collection))


@overload
def make_hashable(value: Union[List[Any], Set[Any]]) -> Tuple[Any, ...]: ...


@overload
def make_hashable(value: Dict[Any, Any]) -> Tuple[Tuple[Any, Any]]: ...


@overload
def make_hashable(value: Any) -> Any: ...


def make_hashable(value: Any) -> Any:
    if isinstance(value, dict):
        return tuple(sorted((key, make_hashable(value)) for key, value in value.items()))
    elif isinstance(value, (list, tuple, set)):
        return tuple([make_hashable(x) for x in value])
    else:
        return value


def get_prop_or_key(elem, key):
    if isinstance(elem, Mapping):
        return elem.get(key)
    else:
        return getattr(elem, key)


def list_pull(alist, key):
    return list(map(lambda elem: get_prop_or_key(elem, key), alist))


def all_none(kwargs):
    for value in kwargs.values():
        if value is not None:
            return False
    return True


def check_script(path, return_code=0):
    try:
        subprocess.check_output([sys.executable, path])
    except subprocess.CalledProcessError as exc:
        if return_code != 0:
            if exc.returncode == return_code:
                return
        raise


def check_cli_execute_file_job(path, pipeline_fn_name, env_file=None):
    from dagster._core.test_utils import instance_for_test

    with instance_for_test():
        cli_cmd = [
            sys.executable,
            "-m",
            "dagster",
            "pipeline",
            "execute",
            "-f",
            path,
            "-a",
            pipeline_fn_name,
        ]

        if env_file:
            cli_cmd.append("-c")
            cli_cmd.append(env_file)

        try:
            subprocess.check_output(cli_cmd)
        except subprocess.CalledProcessError as cpe:
            print(cpe)  # noqa: T201
            raise cpe


def safe_tempfile_path_unmanaged() -> str:
    # This gets a valid temporary file path in the safest possible way, although there is still no
    # guarantee that another process will not create a file at this path. The NamedTemporaryFile is
    # deleted when the context manager exits and the file object is closed.
    #
    # This is preferable to using NamedTemporaryFile as a context manager and passing the name
    # attribute of the file object around because NamedTemporaryFiles cannot be opened a second time
    # if already open on Windows NT or later:
    # https://docs.python.org/3.8/library/tempfile.html#tempfile.NamedTemporaryFile
    # https://github.com/dagster-io/dagster/issues/1582
    with tempfile.NamedTemporaryFile() as fd:
        path = fd.name
    return Path(path).as_posix()


@contextlib.contextmanager
def safe_tempfile_path() -> Iterator[str]:
    path = None
    try:
        path = safe_tempfile_path_unmanaged()
        yield path
    finally:
        if path is not None and os.path.exists(path):
            os.unlink(path)


@overload
def ensure_gen(thing_or_gen: Generator[T, Any, Any]) -> Generator[T, Any, Any]:
    pass


@overload
def ensure_gen(thing_or_gen: T) -> Generator[T, Any, Any]:
    pass


def ensure_gen(
    thing_or_gen: Union[T, Iterator[T], Generator[T, Any, Any]]
) -> Generator[T, Any, Any]:
    if not inspect.isgenerator(thing_or_gen):
        thing_or_gen = cast(T, thing_or_gen)

        def _gen_thing():
            yield thing_or_gen

        return _gen_thing()

    return thing_or_gen


def ensure_dir(file_path: str) -> str:
    try:
        os.makedirs(file_path)
    except OSError as e:
        if e.errno != errno.EEXIST:
            raise
    return file_path


def ensure_file(path: str) -> str:
    ensure_dir(os.path.dirname(path))
    if not os.path.exists(path):
        touch_file(path)
    return path


def touch_file(path):
    ensure_dir(os.path.dirname(path))
    with open(path, "a", encoding="utf8"):
        os.utime(path, None)


def _kill_on_event(termination_event):
    termination_event.wait()
    send_interrupt()


def send_interrupt():
    if seven.IS_WINDOWS:
        # This will raise a KeyboardInterrupt in python land - meaning this wont be able to
        # interrupt things like sleep()
        thread.interrupt_main()
    else:
        # If on unix send an os level signal to interrupt any situation we may be stuck in
        os.kill(os.getpid(), signal.SIGINT)


# Function to be invoked by daemon thread in processes which seek to be cancellable.
# The motivation for this approach is to be able to exit cleanly on Windows. An alternative
# path is to change how the processes are opened and send CTRL_BREAK signals, which at
# the time of authoring seemed a more costly approach.
#
# Reading for the curious:
#  * https://stackoverflow.com/questions/35772001/how-to-handle-the-signal-in-python-on-windows-machine
#  * https://stefan.sofa-rockers.org/2013/08/15/handling-sub-process-hierarchies-python-linux-os-x/
def start_termination_thread(termination_event):
    check.inst_param(termination_event, "termination_event", ttype=type(multiprocessing.Event()))

    int_thread = threading.Thread(
        target=_kill_on_event, args=(termination_event,), name="kill-on-event"
    )
    int_thread.daemon = True
    int_thread.start()


# Executes the next() function within an instance of the supplied context manager class
# (leaving the context before yielding each result)
def iterate_with_context(
    context_fn: Callable[[], ContextManager[Any]], iterator: Iterator[T]
) -> Iterator[T]:
    while True:
        # Allow interrupts during user code so that we can terminate slow/hanging steps
        with context_fn():
            try:
                next_output = next(iterator)
            except StopIteration:
                return

        yield next_output


def datetime_as_float(dt: datetime.datetime) -> float:
    check.inst_param(dt, "dt", datetime.datetime)
    return float((dt - EPOCH).total_seconds())


T_GeneratedContext = TypeVar("T_GeneratedContext")


class EventGenerationManager(Generic[T_GeneratedContext]):
    """Utility class that wraps an event generator function, that also yields a single instance of
    a typed object.  All events yielded before the typed object are yielded through the method
    `generate_setup_events` and all events yielded after the typed object are yielded through the
    method `generate_teardown_events`.

    This is used to help replace the context managers used in pipeline initialization with
    generators so that we can begin emitting initialization events AND construct a pipeline context
    object, while managing explicit setup/teardown.

    This does require calling `generate_setup_events` AND `generate_teardown_events` in order to
    get the typed object.
    """

    def __init__(
        self,
        generator: Iterator[Union["DagsterEvent", T_GeneratedContext]],
        object_cls: Type[T_GeneratedContext],
        require_object: Optional[bool] = True,
    ):
        self.generator = check.generator(generator)
        self.object_cls: Type[T_GeneratedContext] = check.class_param(object_cls, "object_cls")
        self.require_object = check.bool_param(require_object, "require_object")
        self.object: Optional[T_GeneratedContext] = None
        self.did_setup = False
        self.did_teardown = False

    def generate_setup_events(self) -> Iterator["DagsterEvent"]:
        self.did_setup = True
        try:
            while self.object is None:
                obj = next(self.generator)
                if isinstance(obj, self.object_cls):
                    self.object = obj
                else:
                    yield obj
        except StopIteration:
            if self.require_object:
                check.inst_param(
                    self.object,
                    "self.object",
                    self.object_cls,
                    f"generator never yielded object of type {self.object_cls.__name__}",
                )

    def get_object(self) -> T_GeneratedContext:
        if not self.did_setup:
            check.failed("Called `get_object` before `generate_setup_events`")
        return cast(T_GeneratedContext, self.object)

    def generate_teardown_events(self) -> Iterator["DagsterEvent"]:
        self.did_teardown = True
        if self.object:
            yield from self.generator


def utc_datetime_from_timestamp(timestamp: float) -> datetime.datetime:
    tz = timezone.utc
    return datetime.datetime.fromtimestamp(timestamp, tz=tz)


def utc_datetime_from_naive(dt: datetime.datetime) -> datetime.datetime:
    tz = timezone.utc
    return dt.replace(tzinfo=tz)


def is_enum_value(value: object) -> bool:
    return False if value is None else issubclass(value.__class__, Enum)


def git_repository_root() -> str:
    return subprocess.check_output(["git", "rev-parse", "--show-toplevel"]).decode("utf-8").strip()


def segfault() -> None:
    """Reliable cross-Python version segfault.

    https://bugs.python.org/issue1215#msg143236
    """
    import ctypes

    ctypes.string_at(0)


def find_free_port() -> int:
    with contextlib.closing(socket.socket(socket.AF_INET, socket.SOCK_STREAM)) as s:
        s.bind(("", 0))
        s.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        return s.getsockname()[1]


def is_port_in_use(host, port) -> bool:
    # Similar to the socket options that uvicorn uses to bind ports:
    # https://github.com/encode/uvicorn/blob/62f19c1c39929c84968712c371c9b7b96a041dec/uvicorn/config.py#L565-L566
    sock = socket.socket(family=socket.AF_INET)
    sock.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
    try:
        sock.bind((host, port))
        return False
    except socket.error as e:
        return e.errno == errno.EADDRINUSE
    finally:
        sock.close()


@contextlib.contextmanager
def alter_sys_path(to_add: Sequence[str], to_remove: Sequence[str]) -> Iterator[None]:
    to_restore = [path for path in sys.path]

    # remove paths
    for path in to_remove:
        if path in sys.path:
            sys.path.remove(path)

    # add paths
    for path in to_add:
        sys.path.insert(0, path)

    try:
        yield
    finally:
        sys.path = to_restore


@contextlib.contextmanager
def restore_sys_modules() -> Iterator[None]:
    sys_modules = {k: v for k, v in sys.modules.items()}
    try:
        yield
    finally:
        to_delete = set(sys.modules) - set(sys_modules)
        for key in to_delete:
            del sys.modules[key]


def process_is_alive(pid: int) -> bool:
    if seven.IS_WINDOWS:
        import psutil

        return psutil.pid_exists(pid=pid)
    else:
        try:
            subprocess.check_output(["ps", str(pid)])
        except subprocess.CalledProcessError as exc:
            assert exc.returncode == 1
            return False
        return True


def compose(*args):
    """Compose python functions args such that compose(f, g)(x) is equivalent to f(g(x))."""  # noqa: D402
    # reduce using functional composition over all the arguments, with the identity function as
    # initializer
    return functools.reduce(lambda f, g: lambda x: f(g(x)), args, lambda x: x)


def dict_without_keys(ddict, *keys):
    return {key: value for key, value in ddict.items() if key not in set(keys)}


class Counter:
    def __init__(self):
        self._lock = threading.Lock()
        self._counts = OrderedDict()
        super(Counter, self).__init__()

    def increment(self, key: str):
        with self._lock:
            self._counts[key] = self._counts.get(key, 0) + 1

    def counts(self) -> Mapping[str, int]:
        with self._lock:
            copy = {k: v for k, v in self._counts.items()}
        return copy


traced_counter = contextvars.ContextVar("traced_counts", default=Counter())

T_Callable = TypeVar("T_Callable", bound=Callable)


def traced(func: T_Callable) -> T_Callable:
    """A decorator that keeps track of how many times a function is called."""

    @functools.wraps(func)
    def inner(*args, **kwargs):
        counter = traced_counter.get()
        if counter and isinstance(counter, Counter):
            counter.increment(func.__qualname__)

        return func(*args, **kwargs)

    return cast(T_Callable, inner)


def get_terminate_signal():
    if sys.platform == "win32":
        return signal.SIGTERM
    return signal.SIGKILL


def get_run_crash_explanation(prefix: str, exit_code: int):
    # As per https://docs.python.org/3/library/subprocess.html#subprocess.CompletedProcess.returncode
    # negative exit code means a posix signal
    if exit_code < 0 and -exit_code in [signal.value for signal in Signals]:
        posix_signal = -exit_code
        signal_str = Signals(posix_signal).name
        exit_clause = f"was terminated by signal {posix_signal} ({signal_str})."
        if posix_signal == get_terminate_signal():
            exit_clause = (
                exit_clause
                + " This usually indicates that the process was"
                " killed by the operating system due to running out of"
                " memory. Possible solutions include increasing the"
                " amount of memory available to the run, reducing"
                " the amount of memory used by the ops in the run, or"
                " configuring the executor to run fewer ops concurrently."
            )
    else:
        exit_clause = f"unexpectedly exited with code {exit_code}."

    return prefix + " " + exit_clause


def last_file_comp(path: str) -> str:
    return os.path.basename(os.path.normpath(path))


def is_named_tuple_instance(obj: object) -> TypeGuard[NamedTuple]:
    return isinstance(obj, tuple) and hasattr(obj, "_fields")


def is_named_tuple_subclass(klass: Type[object]) -> TypeGuard[Type[NamedTuple]]:
    return isinstance(klass, type) and issubclass(klass, tuple) and hasattr(klass, "_fields")


@overload
def normalize_to_repository(
    definitions_or_repository: Optional[Union["Definitions", "RepositoryDefinition"]] = ...,
    repository: Optional["RepositoryDefinition"] = ...,
    error_on_none: Literal[True] = ...,
) -> "RepositoryDefinition": ...


@overload
def normalize_to_repository(
    definitions_or_repository: Optional[Union["Definitions", "RepositoryDefinition"]] = ...,
    repository: Optional["RepositoryDefinition"] = ...,
    error_on_none: Literal[False] = ...,
) -> Optional["RepositoryDefinition"]: ...


def normalize_to_repository(
    definitions_or_repository: Optional[Union["Definitions", "RepositoryDefinition"]] = None,
    repository: Optional["RepositoryDefinition"] = None,
    error_on_none: bool = True,
) -> Optional["RepositoryDefinition"]:
    """Normalizes the arguments that take a RepositoryDefinition or Definitions object to a
    RepositoryDefinition.

    This is intended to handle both the case where a single argument takes a
    `Union[RepositoryDefinition, Definitions]` or separate keyword arguments accept
    `RepositoryDefinition` or `Definitions`.
    """
    from dagster._core.definitions.definitions_class import Definitions

    if (definitions_or_repository and repository) or (
        error_on_none and not (definitions_or_repository or repository)
    ):
        check.failed("Exactly one of `definitions` or `repository_def` must be provided.")
    elif isinstance(definitions_or_repository, Definitions):
        return definitions_or_repository.get_repository_def()
    elif definitions_or_repository:
        return definitions_or_repository
    elif repository:
        return repository
    else:
        return None


def xor(a, b):
    return bool(a) != bool(b)


def tail_file(path_or_fd: Union[str, int], should_stop: Callable[[], bool]) -> Iterator[str]:
    with open(path_or_fd, "r") as output_stream:
        while True:
            line = output_stream.readline()
            if line:
                yield line
            elif should_stop():
                break
            else:
                time.sleep(0.01)
