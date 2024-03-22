import os
import random
import re
import string
import uuid
import warnings
from collections import OrderedDict
from concurrent.futures import Future, ThreadPoolExecutor
from contextvars import copy_context
from typing import (
    AbstractSet,
    Any,
    Iterable,
    Mapping,
    Optional,
    Sequence,
    Tuple,
    TypedDict,
    TypeVar,
    Union,
    cast,
)
from weakref import WeakSet

import toposort as toposort_
from typing_extensions import Final

import dagster._check as check
from dagster._utils import library_version_from_core_version, parse_package_version

BACKFILL_TAG_LENGTH = 8

PYTHON_LOGGING_LEVELS_MAPPING: Final[Mapping[str, int]] = OrderedDict(
    {"CRITICAL": 50, "ERROR": 40, "WARNING": 30, "INFO": 20, "DEBUG": 10}
)

PYTHON_LOGGING_LEVELS_ALIASES: Final[Mapping[str, str]] = OrderedDict(
    {"FATAL": "CRITICAL", "WARN": "WARNING"}
)

PYTHON_LOGGING_LEVELS_NAMES = frozenset(
    [
        level_name.lower()
        for level_name in sorted(
            list(PYTHON_LOGGING_LEVELS_MAPPING.keys()) + list(PYTHON_LOGGING_LEVELS_ALIASES.keys())
        )
    ]
)

T = TypeVar("T", bound=Any)


def coerce_valid_log_level(log_level: Union[str, int]) -> int:
    """Convert a log level into an integer for consumption by the low-level Python logging API."""
    if isinstance(log_level, int):
        return log_level
    str_log_level = check.str_param(log_level, "log_level")
    check.invariant(
        str_log_level.lower() in PYTHON_LOGGING_LEVELS_NAMES,
        "Bad value for log level {level}: permissible values are {levels}.".format(
            level=str_log_level,
            levels=", ".join(
                [f"'{level_name.upper()}'" for level_name in PYTHON_LOGGING_LEVELS_NAMES]
            ),
        ),
    )
    str_log_level = PYTHON_LOGGING_LEVELS_ALIASES.get(log_level.upper(), log_level.upper())
    return PYTHON_LOGGING_LEVELS_MAPPING[str_log_level]


def toposort(data: Mapping[T, AbstractSet[T]]) -> Sequence[Sequence[T]]:
    # Workaround a bug in older versions of toposort that choke on frozenset
    data = {k: set(v) if isinstance(v, frozenset) else v for k, v in data.items()}
    return [sorted(list(level)) for level in toposort_.toposort(data)]


def toposort_flatten(data: Mapping[T, AbstractSet[T]]) -> Sequence[T]:
    return [item for level in toposort(data) for item in level]


def make_new_run_id() -> str:
    return str(uuid.uuid4())


def make_new_backfill_id() -> str:
    return "".join(random.choice(string.ascii_lowercase) for x in range(BACKFILL_TAG_LENGTH))


def str_format_list(items: Iterable[object]) -> str:
    return "[{items}]".format(items=", ".join([f"'{item}'" for item in items]))


def str_format_set(items: Iterable[object]) -> str:
    return "[{items}]".format(items=", ".join([f"'{item}'" for item in items]))


def check_dagster_package_version(library_name: str, library_version: str) -> None:
    # This import must be internal in order for this function to be testable
    from dagster.version import __version__

    parsed_lib_version = parse_package_version(library_version)
    if parsed_lib_version.release[0] >= 1:
        if library_version != __version__:
            message = (
                f"Found version mismatch between `dagster` ({__version__})"
                f"and `{library_name}` ({library_version})"
            )
            warnings.warn(message)
    else:
        target_version = library_version_from_core_version(__version__)
        if library_version != target_version:
            message = (
                f"Found version mismatch between `dagster` ({__version__}) "
                f"expected library version ({target_version}) "
                f"and `{library_name}` ({library_version})."
            )
            warnings.warn(message)


def get_env_var_name(env_var_str: str):
    if "=" in env_var_str:
        return env_var_str.split("=", maxsplit=1)[0]
    else:
        return env_var_str


def parse_env_var(env_var_str: str) -> Tuple[str, str]:
    if "=" in env_var_str:
        split = env_var_str.split("=", maxsplit=1)
        return (split[0], split[1])
    else:
        env_var_value = os.getenv(env_var_str)
        if env_var_value is None:
            raise Exception(f"Tried to load environment variable {env_var_str}, but it was not set")
        return (env_var_str, cast(str, env_var_value))


class RequestUtilizationMetrics(TypedDict):
    """A dict of utilization metrics for a threadpool executor. We use generic language in case we use this metrics in a scenario where we switch away from a threadpool executor at a later time."""

    max_concurrent_requests: Optional[int]
    num_running_requests: Optional[int]
    num_queued_requests: Optional[int]


class FuturesAwareThreadPoolExecutor(ThreadPoolExecutor):
    def __init__(
        self,
        max_workers: Optional[int] = None,
        thread_name_prefix: str = "",
        initializer: Any = None,
        initargs: Tuple[Any, ...] = (),
    ) -> None:
        super().__init__(max_workers, thread_name_prefix, initializer, initargs)
        # The default threadpool class doesn't track the futures it creates,
        # so if we want to be able to count the number of running futures, we need to do it ourselves.
        self._tracked_futures: WeakSet[Future] = WeakSet()

    def submit(self, fn, *args, **kwargs) -> Future:
        new_future = super().submit(fn, *args, **kwargs)
        self._tracked_futures.add(new_future)
        return new_future

    @property
    def max_workers(self) -> int:
        return self._max_workers

    @property
    def weak_tracked_futures_count(self) -> int:
        return len(self._tracked_futures)

    @property
    def num_running_futures(self) -> int:
        return sum(1 for f in self._tracked_futures if not f.done()) - self.num_queued_futures

    @property
    def num_queued_futures(self) -> int:
        return self._work_queue.qsize()

    def get_current_utilization_metrics(self) -> RequestUtilizationMetrics:
        return {
            "max_concurrent_requests": self.max_workers,
            "num_running_requests": self.num_running_futures,
            "num_queued_requests": self.num_queued_futures,
        }


class InheritContextThreadPoolExecutor(FuturesAwareThreadPoolExecutor):
    """A ThreadPoolExecutor that copies over contextvars at submit time."""

    def submit(self, fn, *args, **kwargs):
        ctx = copy_context()
        return super().submit(ctx.run, fn, *args, **kwargs)


def is_valid_email(email: str) -> bool:
    regex = r"\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Z|a-z]{2,7}\b"
    return bool(re.fullmatch(regex, email))
