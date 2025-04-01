from concurrent.futures import Future
from typing import Any, Union


def get_future_completion_state_or_err(futures: list[Union[Future, Any]]) -> bool:
    """Given a list of futures (and potentially other objects), return True if all futures are completed.
    If any future has an exception, raise the exception.
    """
    for future in futures:
        if not isinstance(future, Future):
            continue

        if not future.done():
            return False

        exception = future.exception()
        if exception:
            raise exception
    return True
