from typing import TYPE_CHECKING, Callable, Optional, TypeVar

if TYPE_CHECKING:
    from dagster._core.event_api import EventLogRecord

T = TypeVar("T")


def extract_latest(
    *records: Optional["EventLogRecord"], value: Callable[["EventLogRecord"], T] = lambda x: x
) -> Optional[T]:
    """Extracts the latest non-None value from a list of records."""
    sorted_records = sorted(filter(None, records), key=lambda x: x.storage_id)
    for r in sorted_records:
        v = value(r)
        if v is not None:
            return v
    return None
