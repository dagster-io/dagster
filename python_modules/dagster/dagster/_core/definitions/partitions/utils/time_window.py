import base64
from collections.abc import Mapping, Sequence
from datetime import datetime
from enum import Enum
from functools import cached_property
from typing import TYPE_CHECKING, NamedTuple

import dagster._check as check
from dagster._annotations import PublicAttr
from dagster._core.definitions.timestamp import TimestampWithTimezone
from dagster._record import record
from dagster._serdes import deserialize_value, serialize_value, whitelist_for_serdes
from dagster._time import get_timezone

if TYPE_CHECKING:
    from dagster._core.definitions.partitions.subset.time_window import TimeWindowPartitionsSubset


@whitelist_for_serdes
@record
class TimeWindowCursor:
    start_timestamp: int
    end_timestamp: int
    offset_partition_count: int

    def __str__(self) -> str:
        return self.to_string()

    def to_string(self) -> str:
        string_serialized = serialize_value(self)
        return base64.b64encode(bytes(string_serialized, encoding="utf-8")).decode("utf-8")

    @classmethod
    def from_cursor(cls, cursor: str):
        return deserialize_value(base64.b64decode(cursor).decode("utf-8"), cls)


class TimeWindow(NamedTuple):
    """An interval that is closed at the start and open at the end.

    Args:
        start (datetime): A datetime that marks the start of the window.
        end (datetime): A datetime that marks the end of the window.
    """

    start: PublicAttr[datetime]
    end: PublicAttr[datetime]


class PartitionRangeStatus(Enum):
    MATERIALIZING = "MATERIALIZING"
    MATERIALIZED = "MATERIALIZED"
    FAILED = "FAILED"


class PartitionTimeWindowStatus:
    def __init__(self, time_window: TimeWindow, status: PartitionRangeStatus):
        self.time_window = time_window
        self.status = status

    def __repr__(self):
        return f"({self.time_window.start} - {self.time_window.end}): {self.status.value}"

    def __eq__(self, other):
        return (
            isinstance(other, PartitionTimeWindowStatus)
            and self.time_window == other.time_window
            and self.status == other.status
        )


@whitelist_for_serdes(
    storage_name="TimeWindow",  # For back-compat with existing serdes
)
class PersistedTimeWindow(
    NamedTuple(
        "_PersistedTimeWindow", [("start", TimestampWithTimezone), ("end", TimestampWithTimezone)]
    )
):
    """Internal serialized representation of a time interval that is closed at the
    start and open at the end.
    """

    def __new__(
        cls,
        start: TimestampWithTimezone,
        end: TimestampWithTimezone,
    ):
        return super(cls, PersistedTimeWindow).__new__(
            cls,
            start=check.inst_param(start, "start", TimestampWithTimezone),
            end=check.inst_param(end, "end", TimestampWithTimezone),
        )

    @property
    def start_timestamp(self) -> float:
        return self._asdict()["start"].timestamp

    @property
    def end_timestamp(self) -> float:
        return self._asdict()["end"].timestamp

    @cached_property
    def start(self) -> datetime:  # pyright: ignore[reportIncompatibleVariableOverride]
        start_timestamp_with_timezone = self._asdict()["start"]
        return datetime.fromtimestamp(
            start_timestamp_with_timezone.timestamp,
            tz=get_timezone(start_timestamp_with_timezone.timezone),
        )

    @cached_property
    def end(self) -> datetime:  # pyright: ignore[reportIncompatibleVariableOverride]
        end_timestamp_with_timezone = self._asdict()["end"]
        return datetime.fromtimestamp(
            end_timestamp_with_timezone.timestamp,
            tz=get_timezone(end_timestamp_with_timezone.timezone),
        )

    @staticmethod
    def from_public_time_window(tw: TimeWindow, timezone: str):
        return PersistedTimeWindow(
            TimestampWithTimezone(tw.start.timestamp(), timezone),
            TimestampWithTimezone(tw.end.timestamp(), timezone),
        )

    def subtract(self, other: "PersistedTimeWindow") -> Sequence["PersistedTimeWindow"]:
        other_start_timestamp = other.start_timestamp
        start_timestamp = self.start_timestamp
        other_end_timestamp = other.end_timestamp
        end_timestamp = self.end_timestamp

        # Case where the two don't intersect at all - just return self
        # Note that this assumes end is exclusive
        if end_timestamp <= other_start_timestamp or other_end_timestamp <= start_timestamp:
            return [self]

        windows = []

        if other_start_timestamp > start_timestamp:
            windows.append(
                PersistedTimeWindow(start=self._asdict()["start"], end=other._asdict()["start"]),
            )

        if other_end_timestamp < end_timestamp:
            windows.append(
                PersistedTimeWindow(start=other._asdict()["end"], end=self._asdict()["end"])
            )

        return windows

    def to_public_time_window(self) -> TimeWindow:
        """Used for exposing TimeWindows over the public Dagster API."""
        return TimeWindow(start=self.start, end=self.end)


def _flatten(
    high_pri_time_windows: list[PartitionTimeWindowStatus],
    low_pri_time_windows: list[PartitionTimeWindowStatus],
) -> list[PartitionTimeWindowStatus]:
    high_pri_time_windows = sorted(high_pri_time_windows, key=lambda t: t.time_window.start)
    low_pri_time_windows = sorted(low_pri_time_windows, key=lambda t: t.time_window.start)

    high_pri_idx = 0
    low_pri_idx = 0

    filtered_low_pri: list[PartitionTimeWindowStatus] = []

    # slice and dice the low pri time windows so there's no overlap with high pri
    while True:
        if low_pri_idx >= len(low_pri_time_windows):
            # reached end of materialized
            break
        if high_pri_idx >= len(high_pri_time_windows):
            # reached end of failed, add all remaining materialized bc there's no overlap
            filtered_low_pri.extend(low_pri_time_windows[low_pri_idx:])
            break

        low_pri_tw = low_pri_time_windows[low_pri_idx]
        high_pri_tw = high_pri_time_windows[high_pri_idx]

        if low_pri_tw.time_window.start.timestamp() < high_pri_tw.time_window.start.timestamp():
            if low_pri_tw.time_window.end.timestamp() <= high_pri_tw.time_window.start.timestamp():
                # low_pri_tw is entirely before high pri
                filtered_low_pri.append(low_pri_tw)
                low_pri_idx += 1
            else:
                # high pri cuts the low pri short
                filtered_low_pri.append(
                    PartitionTimeWindowStatus(
                        TimeWindow(
                            low_pri_tw.time_window.start,
                            high_pri_tw.time_window.start,
                        ),
                        low_pri_tw.status,
                    )
                )

                if low_pri_tw.time_window.end.timestamp() > high_pri_tw.time_window.end.timestamp():
                    # the low pri time window will continue on the other end of the high pri
                    # and get split in two. Modify low_pri[low_pri_idx] to be
                    # the second half of the low pri time window. It will be added in the next iteration.
                    # (don't add it now, because we need to check if it overlaps with the next high pri)
                    low_pri_time_windows[low_pri_idx] = PartitionTimeWindowStatus(
                        TimeWindow(high_pri_tw.time_window.end, low_pri_tw.time_window.end),
                        low_pri_tw.status,
                    )
                    high_pri_idx += 1
                else:
                    # the rest of the low pri time window is inside the high pri time window
                    low_pri_idx += 1
        else:
            if low_pri_tw.time_window.start.timestamp() >= high_pri_tw.time_window.end.timestamp():
                # high pri is entirely before low pri. The next high pri may overlap
                high_pri_idx += 1
            elif low_pri_tw.time_window.end.timestamp() <= high_pri_tw.time_window.end.timestamp():
                # low pri is entirely within high pri, skip it
                low_pri_idx += 1
            else:
                # high pri cuts out the start of the low pri. It will continue on the other end.
                # Modify low_pri[low_pri_idx] to shorten the start. It will be added
                # in the next iteration. (don't add it now, because we need to check if it overlaps with the next high pri)
                low_pri_time_windows[low_pri_idx] = PartitionTimeWindowStatus(
                    TimeWindow(high_pri_tw.time_window.end, low_pri_tw.time_window.end),
                    low_pri_tw.status,
                )
                high_pri_idx += 1

    # combine the high pri windwos with the filtered low pri windows
    flattened_time_windows = high_pri_time_windows
    flattened_time_windows.extend(filtered_low_pri)
    flattened_time_windows.sort(key=lambda t: t.time_window.start)
    return flattened_time_windows


PARTITION_RANGE_STATUS_PRIORITY = [
    PartitionRangeStatus.MATERIALIZING,
    PartitionRangeStatus.FAILED,
    PartitionRangeStatus.MATERIALIZED,
]


def fetch_flattened_time_window_ranges(
    subsets: Mapping[PartitionRangeStatus, "TimeWindowPartitionsSubset"],
) -> Sequence[PartitionTimeWindowStatus]:
    """Given potentially overlapping subsets, return a flattened list of timewindows where the highest priority status wins
    on overlaps.
    """
    prioritized_subsets = sorted(
        [(status, subset) for status, subset in subsets.items()],
        key=lambda t: PARTITION_RANGE_STATUS_PRIORITY.index(t[0]),
    )

    # progressively add lower priority time windows to the list of higher priority time windows
    flattened_time_window_statuses = []
    for status, subset in prioritized_subsets:
        subset_time_window_statuses = [
            PartitionTimeWindowStatus(tw.to_public_time_window(), status)
            for tw in subset.included_time_windows
        ]
        flattened_time_window_statuses = _flatten(
            flattened_time_window_statuses, subset_time_window_statuses
        )

    return flattened_time_window_statuses
