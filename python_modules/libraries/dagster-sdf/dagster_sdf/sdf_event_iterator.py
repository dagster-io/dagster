from collections import abc
from typing import TYPE_CHECKING, Generic, Iterator, Union

from dagster import AssetCheckResult, AssetMaterialization, AssetObservation, Output
from typing_extensions import TypeVar

if TYPE_CHECKING:
    from dagster_sdf.sdf_cli_invocation import SdfCliInvocation

SdfDagsterEventType = Union[Output, AssetMaterialization, AssetObservation, AssetCheckResult]

# We define SdfEventIterator as a generic type for the sake of type hinting.
# This is so that users who inspect the type of the return value of `SdfCliInvocation.stream()`
# will be able to see the inner type of the iterator, rather than just `SdfEventIterator`.
T = TypeVar("T", bound=SdfDagsterEventType)


class SdfEventIterator(Generic[T], abc.Iterator):
    """A wrapper around an iterator of sdf events which contains additional methods for
    post-processing the events.
    """

    def __init__(
        self,
        exec_events: Iterator[T],
        sdf_cli_invocation: "SdfCliInvocation",
    ) -> None:
        self._inner_iterator = exec_events
        self._sdf_cli_invocation = sdf_cli_invocation

    def __next__(self) -> T:
        return next(self._inner_iterator)

    def __iter__(self) -> "SdfEventIterator[T]":
        return self
