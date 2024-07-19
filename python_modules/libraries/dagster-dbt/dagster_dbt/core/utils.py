from collections import deque
from concurrent.futures import Future, ThreadPoolExecutor, TimeoutError
from typing import Any, Callable, Iterator, List, TypeVar, Union


def get_future_completion_state_or_err(futures: List[Union[Future, Any]]) -> bool:
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
    def _apply_func_to_iterator_results(iterable: Iterator[T]) -> None:
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
