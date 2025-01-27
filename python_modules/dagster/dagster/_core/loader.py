from abc import ABC, abstractmethod
from collections.abc import Iterable
from functools import partial
from typing import TYPE_CHECKING, Generic, Optional, TypeVar

from typing_extensions import Self

import dagster._check as check
from dagster._utils.aiodataloader import BlockingDataLoader, DataLoader

TResult = TypeVar("TResult")
TKey = TypeVar("TKey")


if TYPE_CHECKING:
    from dagster._core.instance import DagsterInstance

"""
Loadable - asyncio driven batching

    When resolving a GraphQL operation, it is common to end up with a pattern where a
    set of objects are resolved, and then a field on those objects requires fetching
    a related object by id. To avoid serially fetching those objects by id, something
    must be done. In this past, this batching was solved by manual bespoke classes.

    Loadable is an abstraction that replaces this explicit batching with an implicit scheme
    leveraging the asyncio event loop.

    Within a LoadingContext, requests for the same Loadable object are routed through a shared
    DataLoader instance. This instance accumulates requests that happen in the same event loop
    pass and batches them together. Any subsequent requests for the same ID in the same
    LoadingContext will be served from an in memory cache. This means that mutations need to
    clear the LoadingContext cache.

    The Loadable interface is two methods, `gen` for fetching a single object by its id
    and `gen_many` for loading N by their ids. The "gen" (for generator)[1] name is chosen
    to stand out and make it clear that the method needs to be awaited, which at this time
    is anomalous in a codebase where async is rarely used.

Additional resources:
* https://xuorig.medium.com/the-graphql-dataloader-pattern-visualized-3064a00f319f
[1] Brought to you by the 201X Facebook codebase
"""


class LoadingContext(ABC):
    """A scoped object in which Loadable objects will be fetched in batches and cached.

    Expected to be implemented by request scoped context objects that have access to the DagsterInstance.
    """

    @property
    @abstractmethod
    def instance(self) -> "DagsterInstance":
        raise NotImplementedError()

    @property
    @abstractmethod
    def loaders(self) -> dict[type, tuple[DataLoader, BlockingDataLoader]]:
        raise NotImplementedError()

    def get_loaders_for(self, ttype: type["LoadableBy"]) -> tuple[DataLoader, BlockingDataLoader]:
        if ttype not in self.loaders:
            if not issubclass(ttype, LoadableBy):
                check.failed(f"{ttype} is not Loadable")

            batch_load_fn = partial(ttype._batch_load, context=self)  # noqa
            blocking_batch_load_fn = partial(ttype._blocking_batch_load, context=self)  # noqa

            self.loaders[ttype] = (
                DataLoader(batch_load_fn=batch_load_fn),
                BlockingDataLoader(batch_load_fn=blocking_batch_load_fn),
            )

        return self.loaders[ttype]

    def clear_loaders(self) -> None:
        for ttype in self.loaders:
            del self.loaders[ttype]


# Expected there may be other "Loadable" base classes based on what is needed to load.


class LoadableBy(ABC, Generic[TKey]):
    """Make An object Loadable by ID of type TKey using a DagsterInstance."""

    @classmethod
    async def _batch_load(
        cls, keys: Iterable[TKey], context: "LoadingContext"
    ) -> Iterable[Optional[Self]]:
        return cls._blocking_batch_load(keys, context)

    @classmethod
    @abstractmethod
    def _blocking_batch_load(
        cls, keys: Iterable[TKey], context: "LoadingContext"
    ) -> Iterable[Optional[Self]]:
        # There is no good way of turning an async function into a sync one that
        # will allow us to execute that sync function inside of a broader async context.
        #
        # In the spirit of allowing incremental migration from a fully-sync pattern to
        # an async one, we provide two separate functions here to allow sync and async
        # calls to coexist.
        raise NotImplementedError()

    @classmethod
    async def gen(cls, context: LoadingContext, id: TKey) -> Optional[Self]:
        """Fetch an object by its id."""
        loader, _ = context.get_loaders_for(cls)
        return await loader.load(id)

    @classmethod
    async def gen_many(
        cls, context: LoadingContext, ids: Iterable[TKey]
    ) -> Iterable[Optional[Self]]:
        """Fetch N objects by their id."""
        loader, _ = context.get_loaders_for(cls)
        return await loader.load_many(ids)

    @classmethod
    def blocking_get(cls, context: LoadingContext, id: TKey) -> Optional[Self]:
        """Fetch an object by its id."""
        _, blocking_loader = context.get_loaders_for(cls)
        return blocking_loader.blocking_load(id)

    @classmethod
    def blocking_get_many(cls, context: LoadingContext, ids: Iterable[TKey]) -> Iterable[Self]:
        """Fetch N objects by their id."""
        # in the future, can consider priming the non-blocking loader with the results of this
        # sync call
        _, blocking_loader = context.get_loaders_for(cls)
        return list(filter(None, blocking_loader.blocking_load_many(ids)))

    @classmethod
    def prepare(cls, context: LoadingContext, ids: Iterable[TKey]) -> None:
        """Ensure the provided ids will be fetched on the next blocking query."""
        _, blocking_loader = context.get_loaders_for(cls)
        blocking_loader.prepare(ids)


class LoadingContextForTest(LoadingContext):
    """Loading context intended to be used in unit tests that would not otherwise construct a LoadingContext."""

    def __init__(self, instance: "DagsterInstance"):
        self._instance = instance
        self._loaders = {}

    @property
    def instance(self) -> "DagsterInstance":
        return self._instance

    @property
    def loaders(self) -> dict[type, tuple[DataLoader, BlockingDataLoader]]:
        return self._loaders
