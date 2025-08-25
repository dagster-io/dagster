import datetime
from collections.abc import Iterator
from contextlib import contextmanager
from contextvars import ContextVar
from functools import wraps
from typing import TYPE_CHECKING, Annotated, Callable, Optional, Protocol, TypeVar

from dagster_shared.record import ImportFrom, replace
from typing_extensions import Concatenate, ParamSpec

import dagster._check as check
from dagster._core.definitions.temporal_context import TemporalContext
from dagster._record import record
from dagster._time import get_current_datetime

if TYPE_CHECKING:
    from dagster._core.instance import DynamicPartitionsStore

P = ParamSpec("P")
T_Return = TypeVar("T_Return")


@record
class PartitionLoadingContext:
    """PartitionLoadingContext is a context object that is passed the partition keys functions of a
    PartitionedJobDefinition. It contains information about where partitions are being loaded from
    and the effective time for the partition loading.

    temporal_context (TemporalContext): The TemporalContext for partition loading.
    dynamic_partitions_store: The DynamicPartitionsStore backing the partition loading.  Used for dynamic partitions definitions.
    """

    temporal_context: TemporalContext
    dynamic_partitions_store: Optional[
        Annotated["DynamicPartitionsStore", ImportFrom("dagster._core.instance")]
    ]

    @property
    def effective_dt(self) -> datetime.datetime:
        return self.temporal_context.effective_dt

    def updated(
        self,
        effective_dt: Optional[datetime.datetime],
        dynamic_partitions_store: Optional["DynamicPartitionsStore"],
    ) -> "PartitionLoadingContext":
        """Returns a new PartitionLoadingContext with the updated effective_dt and dynamic_partitions_store.
        If the effective_dt and dynamic_partitions_store are unset, the existing context is returned.

        Args:
            effective_dt: The effective time for the partition loading.
            dynamic_partitions_store: The DynamicPartitionsStore backing the partition loading.
        """
        if effective_dt is None and dynamic_partitions_store is None:
            return self

        return replace(
            self,
            temporal_context=replace(
                self.temporal_context, effective_dt=effective_dt or self.effective_dt
            ),
            dynamic_partitions_store=dynamic_partitions_store or self.dynamic_partitions_store,
        )


_current_ctx: ContextVar[Optional[PartitionLoadingContext]] = ContextVar(
    "current_partition_loading_context", default=None
)


def require_full_partition_loading_context(func: Callable[P, T_Return]) -> Callable[P, T_Return]:
    @wraps(func)
    def wrapper(*args: P.args, **kwargs: P.kwargs) -> T_Return:
        current_context = _current_ctx.get()
        check.invariant(
            current_context is not None
            and current_context.effective_dt is not None
            and current_context.dynamic_partitions_store is not None,
            "This function can only be called within a partition_loading_context with both a datetime and dynamic_partitions_store set",
        )
        return func(*args, **kwargs)

    return wrapper


@contextmanager
def partition_loading_context(
    effective_dt: Optional[datetime.datetime] = None,
    dynamic_partitions_store: Optional["DynamicPartitionsStore"] = None,
    *,
    new_ctx: Optional[PartitionLoadingContext] = None,
) -> Iterator[PartitionLoadingContext]:
    """Context manager for setting the current partition loading context. The information is used
    throughout a variety of PartitionsDefinition, PartitionMapping, and PartitionSubset methods.

    Args:
        effective_dt: The effective time for the partition loading.
        dynamic_partitions_store: The DynamicPartitionsStore backing the partition loading.
        ctx: The current partition loading context.
    """
    prev_ctx = _current_ctx.get() or PartitionLoadingContext(
        temporal_context=TemporalContext(effective_dt=get_current_datetime(), last_event_id=None),
        dynamic_partitions_store=None,
    )
    new_ctx = new_ctx or PartitionLoadingContext.updated(
        prev_ctx, effective_dt, dynamic_partitions_store
    )

    token = _current_ctx.set(new_ctx)

    try:
        yield new_ctx
    finally:
        _current_ctx.reset(token)


class _HasPartitionLoadingContext(Protocol):
    _partition_loading_context: PartitionLoadingContext


Self = TypeVar("Self", bound=_HasPartitionLoadingContext)


def use_partition_loading_context(
    func: Callable[Concatenate[Self, P], T_Return],
) -> Callable[Concatenate[Self, P], T_Return]:
    """Decorator for methods that will use the partition loading context."""

    @wraps(func)
    def wrapper(self: Self, *args: P.args, **kwargs: P.kwargs) -> T_Return:
        with partition_loading_context(new_ctx=self._partition_loading_context):
            return func(self, *args, **kwargs)

    return wrapper
