import os
import random
import re
import string
import uuid
from collections import OrderedDict, deque
from collections.abc import Iterable, Iterator, Mapping, Sequence
from concurrent.futures import Future, ThreadPoolExecutor, TimeoutError
from contextvars import copy_context
from typing import (  # noqa: UP035
    AbstractSet,
    Any,
    Callable,
    Final,
    Optional,
    TypedDict,
    TypeVar,
    Union,
    cast,
)
from weakref import WeakSet

import toposort as toposort_

import dagster._check as check

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


def toposort(
    data: Mapping[T, AbstractSet[T]], sort_key: Optional[Callable[[T], Any]] = None
) -> Sequence[Sequence[T]]:
    # Workaround a bug in older versions of toposort that choke on frozenset
    data = {k: set(v) if isinstance(v, frozenset) else v for k, v in data.items()}
    return [sorted(list(level), key=sort_key) for level in toposort_.toposort(data)]


def toposort_flatten(data: Mapping[T, AbstractSet[T]]) -> Sequence[T]:
    return [item for level in toposort(data) for item in level]


def make_new_run_id() -> str:
    return str(uuid.uuid4())


def is_valid_run_id(run_id: str):
    try:
        uuid.UUID(run_id, version=4)
        return True
    except ValueError:
        return False


def make_new_backfill_id() -> str:
    return "".join(random.choice(string.ascii_lowercase) for x in range(BACKFILL_TAG_LENGTH))


def str_format_list(items: Iterable[object]) -> str:
    return "[{items}]".format(items=", ".join([f"'{item}'" for item in items]))


def str_format_set(items: Iterable[object]) -> str:
    return "[{items}]".format(items=", ".join([f"'{item}'" for item in items]))


def get_env_var_name(env_var_str: str):
    if "=" in env_var_str:
        return env_var_str.split("=", maxsplit=1)[0]
    else:
        return env_var_str


def parse_env_var(env_var_str: str) -> tuple[str, str]:
    if "=" in env_var_str:
        split = env_var_str.split("=", maxsplit=1)
        return (split[0], split[1])
    else:
        env_var_value = os.getenv(env_var_str)
        if env_var_value is None:
            raise Exception(f"Tried to load environment variable {env_var_str}, but it was not set")
        return (env_var_str, cast("str", env_var_value))


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
        initargs: tuple[Any, ...] = (),
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


T = TypeVar("T")
P = TypeVar("P")


def imap(
    executor: ThreadPoolExecutor,
    iterable: Iterator[T],
    func: Callable[[T], P],
) -> Iterator[P]:
    """A version of `concurrent.futures.ThreadpoolExecutor.map` which tails the input iterator in
    a separate thread. This means that the map function can begin processing and yielding results from
    the first elements of the iterator before the iterator is fully consumed.

    Args:
        executor: The ThreadPoolExecutor to use for parallel execution.
        iterable: The iterator to apply the function to.
        func: The function to apply to each element of the iterator.
    """
    work_queue: deque[Future] = deque([])

    # create a small task which waits on the iterator
    # and enqueues work items as they become available
    def _apply_func_to_iterator_results(iterable: Iterator) -> None:
        for arg in iterable:
            work_queue.append(executor.submit(func, arg))

    enqueuing_task = executor.submit(
        _apply_func_to_iterator_results,
        iterable,
    )

    while True:
        if (not enqueuing_task or enqueuing_task.done()) and len(work_queue) == 0:
            break

        if len(work_queue) > 0:
            current_work_item = work_queue[0]

            try:
                yield current_work_item.result(timeout=0.1)
                work_queue.popleft()
            except TimeoutError:
                pass

    # Ensure any exceptions from the enqueuing task processing the iterator are raised,
    # after all work items have been processed.
    exc = enqueuing_task.exception()
    if exc:
        raise exc


def exhaust_iterator_and_yield_results_with_exception(iterable: Iterator[T]) -> Iterator[T]:
    """Fully exhausts an iterator and then yield its results. If the iterator raises an exception,
    raise that exception at the position in the iterator where it was originally raised.

    This is useful if we want to exhaust an iterator, but don't want to discard the elements
    that were yielded before the exception was raised.
    """
    results = []
    caught_exception = None
    try:
        for result in iterable:
            results.append(result)
    except Exception as e:
        caught_exception = e

    yield from results
    if caught_exception:
        raise caught_exception
