from typing import TYPE_CHECKING, Iterator, Union

from dagster import AssetMaterialization, MaterializeResult
from typing_extensions import TypeVar

if TYPE_CHECKING:
    from dagster_fivetran.resources import FivetranWorkspace


FivetranEventType = Union[AssetMaterialization, MaterializeResult]
T = TypeVar("T", bound=FivetranEventType)


class FivetranEventIterator(Iterator[T]):
    """A wrapper around an iterator of Fivetran events which contains additional methods for
    post-processing the events, such as fetching column metadata.
    """

    def __init__(
        self,
        events: Iterator[T],
        fivetran_workspace: "FivetranWorkspace",
    ) -> None:
        self._inner_iterator = events
        self._fivetran_workspace = fivetran_workspace

    def __next__(self) -> T:
        return next(self._inner_iterator)

    def __iter__(self) -> "FivetranEventIterator[T]":
        return self
