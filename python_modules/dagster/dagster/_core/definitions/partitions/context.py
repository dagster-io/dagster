import datetime
from abc import ABC, abstractmethod
from collections.abc import Iterator
from contextlib import contextmanager
from contextvars import ContextVar
from functools import wraps
from typing import TYPE_CHECKING, Annotated, Any, Callable, Optional

from dagster_shared import check
from dagster_shared.record import ImportFrom, replace

from dagster._core.definitions.temporal_context import TemporalContext
from dagster._record import record
from dagster._time import get_current_datetime

if TYPE_CHECKING:
    from dagster._core.instance import DynamicPartitionsStore


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

    @staticmethod
    def default() -> "PartitionLoadingContext":
        return PartitionLoadingContext(
            temporal_context=TemporalContext(
                effective_dt=get_current_datetime(), last_event_id=None
            ),
            dynamic_partitions_store=None,
        )

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
    prev_ctx = _current_ctx.get() or PartitionLoadingContext.default()
    new_ctx = new_ctx or PartitionLoadingContext.updated(
        prev_ctx, effective_dt, dynamic_partitions_store
    )

    token = _current_ctx.set(new_ctx)

    try:
        yield new_ctx
    finally:
        _current_ctx.reset(token)


class HasPartitionLoadingContext(ABC):
    """Mixin for objects that have a PartitionLoadingContext."""

    @property
    @abstractmethod
    def _partition_loading_context(self) -> PartitionLoadingContext: ...


def use_partition_loading_context(func: Callable[..., Any]) -> Callable[..., Any]:
    """Decorator for class methods of HasPartitionLoadingContext that will use the partition loading context."""

    @wraps(func)
    def wrapper(self: HasPartitionLoadingContext, *args: Any, **kwargs: Any) -> Any:
        with partition_loading_context(new_ctx=self._partition_loading_context):
            return func(self, *args, **kwargs)

    return wrapper


def requires_partition_loading_context(func: Callable[..., Any]) -> Callable[..., Any]:
    """Decorator marking that a function must have a partition loading context available."""

    @wraps(func)
    def wrapper(*args: Any, **kwargs: Any) -> Any:
        ctx = _current_ctx.get()
        check.invariant(
            ctx is not None,
            "Attempted to call a function that requires the partition loading context to be set. "
            "Use the `with partition_loading_context(...):` context manager to set the context.",
        )
        check.invariant(
            ctx and ctx.dynamic_partitions_store is not None,
            "No dynamic partitions store is available in the current partition loading context. "
            "Use the `with partition_loading_context(...):` context manager to add a dynamic "
            "partitions store to the context.",
        )
        return func(*args, **kwargs)

    return wrapper
