import asyncio
import time
from collections.abc import Awaitable, Iterator, Mapping, Sequence
from typing import Callable, Optional, TypeVar

import dagster._check as check

T = TypeVar("T")


def exponential_delay_generator(
    base_delay: float = 0.1, backoff_factor: float = 2.0
) -> Iterator[float]:
    i = base_delay
    while True:
        yield i
        i = i * backoff_factor


BACKOFF_MAX_RETRIES = 4


def backoff(
    fn: Callable[..., T],
    retry_on: tuple[type[BaseException], ...],
    args: Optional[Sequence[object]] = None,
    kwargs: Optional[Mapping[str, object]] = None,
    max_retries: int = BACKOFF_MAX_RETRIES,
    delay_generator: Optional[Iterator[float]] = None,
) -> T:
    """Straightforward backoff implementation.

    Note that this doesn't implement any jitter on the delays, so probably won't be appropriate for very
    parallel situations.

    Args:
        fn (Callable): The function to wrap in a backoff/retry loop.
        retry_on (Tuple[Exception, ...]): The exception classes on which to retry. Note that we don't (yet)
            have any support for matching the exception messages.
        args (Optional[List[Any]]): Positional args to pass to the callable.
        kwargs (Optional[Dict[str, Any]]): Keyword args to pass to the callable.
        max_retries (Optional[Int]): The maximum number of times to retry a failed fn call. Set to 0 for no backoff.
            Default: 4
        delay_generator (Generator[float, None, None]): Generates the successive delays between retry attempts.
    """
    check.callable_param(fn, "fn")
    retry_on = check.tuple_param(retry_on, "retry_on")
    args = check.opt_sequence_param(args, "args")
    kwargs = check.opt_mapping_param(kwargs, "kwargs", key_type=str)
    check.int_param(max_retries, "max_retries")
    check.opt_generator_param(delay_generator, "delay_generator")

    if not delay_generator:
        delay_generator = exponential_delay_generator()

    retries = 0

    to_raise = None

    try:
        return fn(*args, **kwargs)
    except retry_on as exc:
        to_raise = exc

    while retries < max_retries:
        time.sleep(next(delay_generator))
        try:
            return fn(*args, **kwargs)
        except retry_on as exc:
            retries += 1
            to_raise = exc
            continue

    raise to_raise


async def async_backoff(
    fn: Callable[..., Awaitable[T]],
    retry_on: Callable[[BaseException], bool],
    args: Optional[Sequence[object]] = None,
    kwargs: Optional[Mapping[str, object]] = None,
    max_retries: int = BACKOFF_MAX_RETRIES,
    delay_generator: Optional[Iterator[float]] = None,
) -> T:
    """Async backoff implementation with configurable retry predicate.

    Args:
        fn: The async function to wrap in a backoff/retry loop.
        retry_on: Function that takes a BaseException and returns True if retry should be attempted.
        args: Positional args to pass to the callable.
        kwargs: Keyword args to pass to the callable.
        max_retries: The maximum number of times to retry a failed fn call. Set to 0 for no backoff.
        delay_generator: Generates the successive delays between retry attempts.
    """
    check.callable_param(fn, "fn")
    check.callable_param(retry_on, "retry_on")
    args = check.opt_sequence_param(args, "args")
    kwargs = check.opt_mapping_param(kwargs, "kwargs", key_type=str)
    check.int_param(max_retries, "max_retries")
    check.opt_generator_param(delay_generator, "delay_generator")

    if not delay_generator:
        delay_generator = exponential_delay_generator()

    retries = 0
    to_raise = None

    try:
        return await fn(*args, **kwargs)
    except BaseException as exc:
        if not retry_on(exc):
            raise
        to_raise = exc

    while retries < max_retries:
        await asyncio.sleep(next(delay_generator))
        try:
            return await fn(*args, **kwargs)
        except BaseException as exc:
            if not retry_on(exc):
                raise
            retries += 1
            to_raise = exc
            continue

    raise to_raise
