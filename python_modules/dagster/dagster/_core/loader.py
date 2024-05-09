from abc import ABC, abstractmethod
from functools import partial
from typing import TYPE_CHECKING, Dict, Generic, Iterable, Optional, Type, TypeVar

from typing_extensions import Self

import dagster._check as check
from dagster._utils.aiodataloader import DataLoader

TResult = TypeVar("TResult")
TKey = TypeVar("TKey")


if TYPE_CHECKING:
    from .instance import DagsterInstance

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
    def loaders(self) -> Dict[Type, DataLoader]:
        raise NotImplementedError()

    def get_loader_for(self, ttype: Type["InstanceLoadableBy"]) -> DataLoader:
        if ttype not in self.loaders:
            if not issubclass(ttype, InstanceLoadableBy):
                check.failed(f"{ttype} is not Loadable")

            self.loaders[ttype] = DataLoader(
                batch_load_fn=partial(
                    ttype._batch_load,  # noqa
                    instance=self.instance,
                ),
            )

        return self.loaders[ttype]


# Expected there may be other "Loadable" base classes based on what is needed to load.


class InstanceLoadableBy(ABC, Generic[TKey]):
    """Make An object Loadable by ID of type TKey using a DagsterInstance."""

    @classmethod
    @abstractmethod
    async def _batch_load(
        cls,
        keys: Iterable[TKey],
        instance: "DagsterInstance",
    ) -> Iterable[Optional[Self]]:
        raise NotImplementedError()

    @classmethod
    async def gen(cls, context: LoadingContext, id: TKey) -> Self:
        """Fetch an object by its id."""
        loader = context.get_loader_for(cls)
        return await loader.load(id)

    @classmethod
    async def gen_many(
        cls, context: LoadingContext, ids: Iterable[TKey]
    ) -> Iterable[Optional[Self]]:
        """Fetch N objects by their id."""
        loader = context.get_loader_for(cls)
        return await loader.load_many(ids)
