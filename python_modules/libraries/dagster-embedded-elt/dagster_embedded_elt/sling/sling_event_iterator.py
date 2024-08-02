from collections import abc
from typing import TYPE_CHECKING, Any, Dict, Generic, Iterator

from dagster import AssetMaterialization
from typing_extensions import TypeVar

if TYPE_CHECKING:
    from .resources import SlingResource


SlingEventType = AssetMaterialization

# We define DbtEventIterator as a generic type for the sake of type hinting.
# This is so that users who inspect the type of the return value of `DbtCliInvocation.stream()`
# will be able to see the inner type of the iterator, rather than just `DbtEventIterator`.
T = TypeVar("T", bound=SlingEventType)


class SlingEventIterator(Generic[T], abc.Iterator):
    """A wrapper around an iterator of ling events which contains additional methods for
    post-processing the events, such as fetching column metadata.
    """

    def __init__(
        self, events: Iterator[T], sling_cli: "SlingResource", replication_config: Dict[str, Any]
    ) -> None:
        self._inner_iterator = events
        self._sling_cli = sling_cli
        self._replication_config = replication_config

    def __next__(self) -> T:
        return next(self._inner_iterator)

    def __iter__(self) -> "SlingEventIterator[T]":
        return self
