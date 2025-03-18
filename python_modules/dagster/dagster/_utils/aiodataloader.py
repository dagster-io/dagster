# Copied from https://github.com/syrusakbary/aiodataloader

import sys
from asyncio import (
    AbstractEventLoop,
    Future,
    ensure_future,
    gather,
    get_event_loop,
    iscoroutine,
    iscoroutinefunction,
)
from collections import namedtuple
from collections.abc import Coroutine, Iterable, Iterator, MutableMapping
from functools import partial
from typing import Any, Callable, Generic, Optional, TypeVar, Union

if sys.version_info >= (3, 10):
    from typing import TypeGuard
else:
    from typing_extensions import TypeGuard

__version__ = "0.4.0"

KeyT = TypeVar("KeyT")
ReturnT = TypeVar("ReturnT")
CacheKeyT = TypeVar("CacheKeyT")
DataLoaderT = TypeVar("DataLoaderT", bound="DataLoader[Any, Any]")
T = TypeVar("T")


def iscoroutinefunctionorpartial(
    fn: Union[Callable[..., ReturnT], "partial[ReturnT]"],
) -> TypeGuard[Callable[..., Coroutine[Any, Any, ReturnT]]]:
    return iscoroutinefunction(fn.func if isinstance(fn, partial) else fn)


Loader = namedtuple("Loader", "key,future")


class _BaseDataLoader(Generic[KeyT, ReturnT]):
    def __init__(
        self,
        batch_load_fn: Callable[[Iterable[KeyT]], Coroutine[Any, Any, Iterable[ReturnT]]],
        max_batch_size: Optional[int] = None,
    ):
        self.max_batch_size = max_batch_size


class BlockingDataLoader(Generic[KeyT, ReturnT]):
    """Currently, the cache is not shared between blocking and non-blocking DataLoaders, as it is
    challenging to drive the event loop properly while managing a shared cache.
    """

    def __init__(
        self,
        batch_load_fn: Callable[[Iterable[KeyT]], Iterable[ReturnT]],
        get_cache_key: Optional[Callable[[KeyT], Union[CacheKeyT, KeyT]]] = None,
        max_batch_size: Optional[int] = None,
    ):
        self._cache = {}
        self._to_query = {}

        self.get_cache_key = get_cache_key or (lambda x: x)

        self.batch_load_fn = batch_load_fn
        self.max_batch_size = max_batch_size

    def prepare(self, keys: Iterable[KeyT]) -> None:
        # ensure that the provided keys will be fetched as a unit in the next fetch
        for key in keys:
            cache_key = self.get_cache_key(key)
            if cache_key not in self._cache:
                self._to_query[cache_key] = key

    def blocking_load(self, key: KeyT) -> ReturnT:
        """Loads the provided key synchronously, pulling from the cache if possible."""
        self.prepare([key])

        if self._to_query:
            for chunk in get_chunks(
                list(self._to_query.values()),
                self.max_batch_size or len(self._to_query),
            ):
                # uses independent event loop from the async system
                chunk_results = self.batch_load_fn(chunk)
                for k, v in zip(chunk, chunk_results):
                    self._cache[self.get_cache_key(k)] = v

        self._to_query = {}
        return self._cache[self.get_cache_key(key)]

    def blocking_load_many(self, keys: Iterable[KeyT]) -> Iterable[ReturnT]:
        self.prepare(keys)
        return [self.blocking_load(key) for key in keys]


class DataLoader(_BaseDataLoader[KeyT, ReturnT]):
    batch: bool = True
    max_batch_size: Optional[int] = None
    cache: Optional[bool] = True

    def __init__(
        self,
        batch_load_fn: Callable[[Iterable[KeyT]], Coroutine[Any, Any, Iterable[ReturnT]]],
        batch: Optional[bool] = None,
        max_batch_size: Optional[int] = None,
        cache: Optional[bool] = None,
        get_cache_key: Optional[Callable[[KeyT], Union[CacheKeyT, KeyT]]] = None,
        cache_map: Optional[MutableMapping[Union[CacheKeyT, KeyT], "Future[ReturnT]"]] = None,
        loop: Optional[AbstractEventLoop] = None,
    ):
        self._loop = loop

        self.batch_load_fn = batch_load_fn

        assert iscoroutinefunctionorpartial(self.batch_load_fn), (
            f"batch_load_fn must be coroutine. Received: {self.batch_load_fn}"
        )

        if not callable(self.batch_load_fn):
            raise TypeError(
                "DataLoader must have a batch_load_fn which accepts "
                f"Iterable<key> and returns Future<Iterable<value>>, but got: {batch_load_fn}."
            )

        if batch is not None:
            self.batch = batch

        if max_batch_size is not None:
            self.max_batch_size = max_batch_size

        if cache is not None:
            self.cache = cache

        if get_cache_key is not None:
            self.get_cache_key = get_cache_key
        if not hasattr(self, "get_cache_key"):
            self.get_cache_key = lambda x: x

        self._cache = cache_map if cache_map is not None else {}
        self._queue: list[Loader] = []

        super().__init__(batch_load_fn, max_batch_size)

    @property
    def loop(self) -> AbstractEventLoop:
        # ensure a good error is thrown if the event loop has changed since instantiation,
        # can result in cryptic errors otherwise.

        # it might be possible to instead update the event loop if there is no work in flight,
        # unclear if there are valid uses cases for that

        if self._loop is None:
            # lazily initialize the loop to allow for cases where this object is constructed
            # outside the context of an event loop (e.g. unit tests)
            self._loop = get_event_loop()

        if self._loop != get_event_loop():
            raise Exception(
                "event loop has changed since init, this DataLoader instance is no longer usable."
            )

        return self._loop

    def load(self, key: KeyT) -> "Future[ReturnT]":
        """Loads a key, returning a `Future` for the value represented by that key."""
        if key is None:
            raise TypeError(
                f"The loader.load() function must be called with a value, but got: {key}."
            )

        cache_key = self.get_cache_key(key)

        # If caching and there is a cache-hit, return cached Future.
        if self.cache:
            cached_result = self._cache.get(cache_key)
            if cached_result:
                return cached_result

        # Otherwise, produce a new Future for this value.
        future = self.loop.create_future()
        # If caching, cache this Future.
        if self.cache:
            self._cache[cache_key] = future

        self.do_resolve_reject(key, future)
        return future

    def do_resolve_reject(self, key: KeyT, future: "Future[ReturnT]") -> None:
        # Enqueue this Future to be dispatched.
        self._queue.append(Loader(key=key, future=future))
        # Determine if a dispatch of this queue should be scheduled.
        # A single dispatch should be scheduled per queue at the time when the
        # queue changes from "empty" to "full".
        if len(self._queue) == 1:
            if self.batch:
                # If batching, schedule a task to dispatch the queue.
                enqueue_post_future_job(self.loop, self)
            else:
                # Otherwise dispatch the (queue of one) immediately.
                dispatch_queue(self)

    def load_many(self, keys: Iterable[KeyT]) -> "Future[list[ReturnT]]":
        """Loads multiple keys, returning a list of values.

        >>> a, b = await my_loader.load_many([ 'a', 'b' ])

        This is equivalent to the more verbose:

        >>> a, b = await gather(
        >>>    my_loader.load('a'),
        >>>    my_loader.load('b')
        >>> )
        """
        if not isinstance(keys, Iterable):
            raise TypeError(
                "The loader.load_many() function must be called with Iterable<key> "
                f"but got: {keys}."
            )

        return gather(*[self.load(key) for key in keys])

    def clear(self: DataLoaderT, key: KeyT) -> DataLoaderT:
        """Clears the value at `key` from the cache, if it exists. Returns itself for
        method chaining.
        """
        cache_key = self.get_cache_key(key)
        self._cache.pop(cache_key, None)
        return self

    def clear_all(self: DataLoaderT) -> DataLoaderT:
        """Clears the entire cache. To be used when some event results in unknown
        invalidations across this particular `DataLoader`. Returns itself for
        method chaining.
        """
        self._cache.clear()
        return self

    def prime(self: DataLoaderT, key: KeyT, value: ReturnT) -> DataLoaderT:
        """Adds the provied key and value to the cache. If the key already exists, no
        change is made. Returns itself for method chaining.
        """
        cache_key = self.get_cache_key(key)

        # Only add the key if it does not already exist.
        if cache_key not in self._cache:
            # Cache a rejected future if the value is an Error, in order to match
            # the behavior of load(key).
            future = self.loop.create_future()
            if isinstance(value, Exception):
                future.set_exception(value)
            else:
                future.set_result(value)

            self._cache[cache_key] = future

        return self


def enqueue_post_future_job(loop: AbstractEventLoop, loader: DataLoader[Any, Any]) -> None:
    async def dispatch() -> None:
        dispatch_queue(loader)

    loop.call_soon(ensure_future, dispatch())


def get_chunks(iterable_obj: list[T], chunk_size: int = 1) -> Iterator[list[T]]:
    chunk_size = max(1, chunk_size)
    return (iterable_obj[i : i + chunk_size] for i in range(0, len(iterable_obj), chunk_size))


def dispatch_queue(loader: DataLoader[Any, Any]) -> None:
    """Given the current state of a Loader instance, perform a batch load
    from its current queue.
    """
    # Take the current loader queue, replacing it with an empty queue.
    queue = loader._queue  # noqa: SLF001
    loader._queue = []  # noqa: SLF001

    # If a max_batch_size was provided and the queue is longer, then segment the
    # queue into multiple batches, otherwise treat the queue as a single batch.
    max_batch_size = loader.max_batch_size

    if max_batch_size and max_batch_size < len(queue):
        chunks = get_chunks(queue, max_batch_size)
        for chunk in chunks:
            # Note: the noqa here might mask a real bug and worthy of investigation
            ensure_future(dispatch_queue_batch(loader, chunk))  # noqa: RUF006
    else:
        ensure_future(dispatch_queue_batch(loader, queue))  # noqa: RUF006


async def dispatch_queue_batch(loader: DataLoader[Any, Any], queue: list[Loader]) -> None:
    # Collect all keys to be loaded in this dispatch
    keys = [ql.key for ql in queue]

    # Call the provided batch_load_fn for this loader with the loader queue's keys.
    try:
        batch_future = loader.batch_load_fn(keys)
    except Exception as e:
        return failed_dispatch(loader, queue, e)

    # Assert the expected response from batch_load_fn
    if not batch_future or not iscoroutine(batch_future):
        return failed_dispatch(
            loader,
            queue,
            TypeError(
                "DataLoader must be constructed with a function which accepts "
                "Iterable<key> and returns Future<Iterable<value>>, but the "
                f"function did not return a Coroutine: {batch_future}."
            ),
        )

    try:
        values = await batch_future
        if not isinstance(values, Iterable):
            raise TypeError(
                "DataLoader must be constructed with a function which accepts "
                "Iterable<key> and returns Future<Iterable<value>>, but the "
                f"function did not return a Future of a Iterable: {values}."
            )

        values = list(values)
        if len(values) != len(keys):
            raise TypeError(
                "DataLoader must be constructed with a function which accepts "
                "Iterable<key> and returns Future<Iterable<value>>, but the "
                "function did not return a Future of a Iterable with the same "
                "length as the Iterable of keys."
                f"\n\nKeys:\n{keys}"
                f"\n\nValues:\n{values}"
            )

        # Step through the values, resolving or rejecting each Future in the
        # loaded queue.
        for ql, value in zip(queue, values):
            if isinstance(value, Exception):
                ql.future.set_exception(value)
            else:
                ql.future.set_result(value)

    except Exception as e:
        return failed_dispatch(loader, queue, e)


def failed_dispatch(loader: DataLoader[Any, Any], queue: list[Loader], error: Exception) -> None:
    """Do not cache individual loads if the entire batch dispatch fails,
    but still reject each request so they do not hang.
    """
    for ql in queue:
        loader.clear(ql.key)
        ql.future.set_exception(error)
