import json
from collections.abc import Iterable, Sequence
from datetime import datetime
from functools import cached_property
from typing import TYPE_CHECKING, Any, NamedTuple, Optional, Union, cast

from dagster_shared.serdes import NamedTupleSerializer

import dagster._check as check
from dagster._annotations import public
from dagster._core.definitions.partitions.context import partition_loading_context
from dagster._core.definitions.partitions.definition.partitions_definition import (
    PartitionsDefinition,
)
from dagster._core.definitions.partitions.definition.time_window import (
    TimeWindowPartitionsDefinition,
)
from dagster._core.definitions.partitions.partition_key_range import PartitionKeyRange
from dagster._core.definitions.partitions.subset.partitions_subset import PartitionsSubset
from dagster._core.definitions.partitions.utils.time_window import PersistedTimeWindow, TimeWindow
from dagster._core.definitions.timestamp import TimestampWithTimezone
from dagster._core.errors import DagsterInvalidDeserializationVersionError
from dagster._serdes import whitelist_for_serdes

if TYPE_CHECKING:
    from dagster._core.definitions.partitions.subset.all import AllPartitionsSubset
    from dagster._core.instance import DynamicPartitionsStore


def _attempt_coerce_to_time_window_subset(subset: "PartitionsSubset") -> "PartitionsSubset":
    """Attempts to convert the input subset into a TimeWindowPartitionsSubset."""
    from dagster._core.definitions.partitions.subset.all import AllPartitionsSubset

    if isinstance(subset, TimeWindowPartitionsSubset):
        return subset
    elif isinstance(subset, TimeWindowPartitionsSubset):
        return TimeWindowPartitionsSubset(
            partitions_def=subset.partitions_def,
            num_partitions=subset.num_partitions,
            included_time_windows=subset.included_time_windows,
        )
    elif isinstance(subset, AllPartitionsSubset) and isinstance(
        subset.partitions_def, TimeWindowPartitionsDefinition
    ):
        return TimeWindowPartitionsSubset.from_all_partitions_subset(subset)
    else:
        return subset


class TimeWindowPartitionsSubsetSerializer(NamedTupleSerializer):
    # TimeWindowPartitionsSubsets have custom logic to delay calculating num_partitions until it
    # is needed to improve performance. When serializing, we want to serialize the number of
    # partitions, so we force calculation.
    def before_pack(self, value: "TimeWindowPartitionsSubset") -> "TimeWindowPartitionsSubset":  # pyright: ignore[reportIncompatibleMethodOverride]
        # value.num_partitions will calculate the number of partitions if the field is None
        # We want to check if the field is None and replace the value with the calculated value
        # for serialization
        if value._asdict()["num_partitions"] is None:
            return TimeWindowPartitionsSubset(
                partitions_def=value.partitions_def,
                num_partitions=value.num_partitions,
                included_time_windows=value.included_time_windows,
            )
        return value

    def before_unpack(self, context, value: dict[str, Any]):  # pyright: ignore[reportIncompatibleMethodOverride]
        num_partitions = value.get("num_partitions")
        # some objects were serialized with an invalid num_partitions, so fix that here
        if num_partitions is not None and num_partitions < 0:
            # set it to None so that it will be recalculated
            value["num_partitions"] = None
        return value


@whitelist_for_serdes(serializer=TimeWindowPartitionsSubsetSerializer)
class TimeWindowPartitionsSubset(
    PartitionsSubset,
    NamedTuple(
        "_TimeWindowPartitionsSubset",
        [
            ("partitions_def", TimeWindowPartitionsDefinition),
            ("num_partitions", Optional[int]),
            ("included_time_windows", Sequence[PersistedTimeWindow]),
        ],
    ),
):
    """A PartitionsSubset for a TimeWindowPartitionsDefinition, which internally represents the
    included partitions using TimeWindows.
    """

    # Every time we change the serialization format, we should increment the version number.
    # This will ensure that we can gracefully degrade when deserializing old data.
    SERIALIZATION_VERSION = 1

    def __new__(
        cls,
        partitions_def: TimeWindowPartitionsDefinition,
        num_partitions: Optional[int],
        included_time_windows: Sequence[Union[PersistedTimeWindow, TimeWindow]],
    ):
        included_time_windows = [
            PersistedTimeWindow.from_public_time_window(tw, partitions_def.timezone)
            if isinstance(tw, TimeWindow)
            else tw
            for tw in included_time_windows
        ]

        return super().__new__(
            cls,
            partitions_def=check.inst_param(
                partitions_def, "partitions_def", TimeWindowPartitionsDefinition
            ),
            num_partitions=check.opt_int_param(num_partitions, "num_partitions"),
            included_time_windows=check.sequence_param(
                included_time_windows, "included_time_windows", of_type=PersistedTimeWindow
            ),
        )

    @staticmethod
    def from_all_partitions_subset(subset: "AllPartitionsSubset") -> "TimeWindowPartitionsSubset":
        partitions_def = check.inst(
            subset.partitions_def,
            TimeWindowPartitionsDefinition,
            "Provided subset must reference a TimeWindowPartitionsDefinition",
        )
        first_window = partitions_def.get_first_partition_window()
        last_window = partitions_def.get_last_partition_window()
        return TimeWindowPartitionsSubset(
            partitions_def=partitions_def,
            included_time_windows=[
                PersistedTimeWindow.from_public_time_window(
                    TimeWindow(first_window.start, last_window.end), partitions_def.timezone
                )
            ]
            if first_window and last_window
            else [],
            num_partitions=None,
        )

    @cached_property
    def included_time_windows(self) -> Sequence[PersistedTimeWindow]:  # pyright: ignore[reportIncompatibleVariableOverride]
        return self._asdict()["included_time_windows"]

    @property
    def first_start(self) -> datetime:
        """The start datetime of the earliest partition in the subset."""
        if len(self.included_time_windows) == 0:
            check.failed("Empty subset")
        return self.included_time_windows[0].start

    @property
    def is_empty(self) -> bool:
        return len(self.included_time_windows) == 0

    def cheap_ends_before(self, dt: datetime, dt_cron_schedule: str) -> bool:
        """Performs a cheap calculation that checks whether the latest window in this subset ends
        before the given dt. If this returns True, then it means the latest window definitely ends
        before the given dt. If this returns False, it means it may or may not end before the given
        dt.

        Args:
            dt_cron_schedule (str): A cron schedule that dt is on one of the ticks of.
        """
        return self.included_time_windows[-1].end_timestamp <= dt.timestamp()

    @cached_property
    def num_partitions(self) -> int:  # pyright: ignore[reportIncompatibleVariableOverride]
        num_partitions_ = self._asdict()["num_partitions"]
        if num_partitions_ is None:
            return sum(
                self.partitions_def.get_num_partitions_in_window(
                    time_window.to_public_time_window()
                )
                for time_window in self.included_time_windows
            )
        return num_partitions_

    @classmethod
    def _num_partitions_from_time_windows(
        cls,
        partitions_def: TimeWindowPartitionsDefinition,
        time_windows: Sequence[PersistedTimeWindow],
    ) -> int:
        return sum(
            len(partitions_def.get_partition_keys_in_time_window(time_window))
            for time_window in time_windows
        )

    def _get_partition_time_windows_not_in_subset(self) -> Sequence[PersistedTimeWindow]:
        """Returns a list of partition time windows that are not in the subset.
        Each time window is a single partition.
        """
        first_tw = self.partitions_def.get_first_partition_window()
        last_tw = self.partitions_def.get_last_partition_window()

        if not first_tw or not last_tw:
            # no partitions
            return []

        last_tw_end_timestamp = last_tw.end.timestamp()
        first_tw_start_timestamp = first_tw.start.timestamp()

        if len(self.included_time_windows) == 0:
            return [
                PersistedTimeWindow.from_public_time_window(
                    TimeWindow(first_tw.start, last_tw.end), self.partitions_def.timezone
                )
            ]

        time_windows = []
        if first_tw_start_timestamp < self.included_time_windows[0].start_timestamp:
            time_windows.append(
                PersistedTimeWindow.from_public_time_window(
                    TimeWindow(first_tw.start, self.included_time_windows[0].start),
                    self.partitions_def.timezone,
                )
            )

        for i in range(len(self.included_time_windows) - 1):
            if self.included_time_windows[i].start_timestamp >= last_tw_end_timestamp:
                break
            if self.included_time_windows[i].end_timestamp < last_tw_end_timestamp:
                if self.included_time_windows[i + 1].start_timestamp <= last_tw_end_timestamp:
                    time_windows.append(
                        PersistedTimeWindow.from_public_time_window(
                            TimeWindow(
                                self.included_time_windows[i].end,
                                self.included_time_windows[i + 1].start,
                            ),
                            self.partitions_def.timezone,
                        )
                    )
                else:
                    time_windows.append(
                        PersistedTimeWindow.from_public_time_window(
                            TimeWindow(
                                self.included_time_windows[i].end,
                                last_tw.end,
                            ),
                            self.partitions_def.timezone,
                        )
                    )

        if last_tw_end_timestamp > self.included_time_windows[-1].end_timestamp:
            time_windows.append(
                PersistedTimeWindow.from_public_time_window(
                    TimeWindow(self.included_time_windows[-1].end, last_tw.end),
                    self.partitions_def.timezone,
                )
            )

        return time_windows

    def get_partition_keys_not_in_subset(
        self, partitions_def: PartitionsDefinition
    ) -> Iterable[str]:
        partition_keys: list[str] = []
        for tw in self._get_partition_time_windows_not_in_subset():
            partition_keys.extend(self.partitions_def.get_partition_keys_in_time_window(tw))
        return partition_keys

    def get_partition_key_ranges(
        self,
        partitions_def: PartitionsDefinition,
        current_time: Optional[datetime] = None,
        dynamic_partitions_store: Optional["DynamicPartitionsStore"] = None,
        respect_bounds: bool = True,
    ) -> Sequence[PartitionKeyRange]:
        with partition_loading_context(current_time, dynamic_partitions_store):
            return [
                self.partitions_def.get_partition_key_range_for_time_window(
                    window.to_public_time_window(), respect_bounds=respect_bounds
                )
                for window in self.included_time_windows
            ]

    def _add_partitions_to_time_windows(
        self,
        initial_windows: Sequence[PersistedTimeWindow],
        partition_keys: Sequence[str],
        validate: bool = True,
    ) -> tuple[Sequence[PersistedTimeWindow], int]:
        """Merges a set of partition keys into an existing set of time windows, returning the
        minimized set of time windows and the number of partitions added.
        """
        result_windows = [*initial_windows]
        time_windows = cast(
            "TimeWindowPartitionsDefinition", self.partitions_def
        ).time_windows_for_partition_keys(frozenset(partition_keys), validate=validate)

        num_added_partitions = 0
        for window in sorted(time_windows, key=lambda tw: tw.start.timestamp()):
            window_start_timestamp = window.start.timestamp()
            # go in reverse order because it's more common to add partitions at the end than the
            # beginning
            for i in reversed(range(len(result_windows))):
                included_window = result_windows[i]
                lt_end_of_range = window_start_timestamp < included_window.end_timestamp
                gte_start_of_range = window_start_timestamp >= included_window.start_timestamp

                if lt_end_of_range and gte_start_of_range:
                    break

                if not lt_end_of_range:
                    merge_with_range = included_window.end_timestamp == window_start_timestamp
                    merge_with_later_range = i + 1 < len(result_windows) and (
                        window.end.timestamp() == result_windows[i + 1].start_timestamp
                    )

                    if merge_with_range and merge_with_later_range:
                        result_windows[i] = PersistedTimeWindow.from_public_time_window(
                            TimeWindow(included_window.start, result_windows[i + 1].end),
                            self.partitions_def.timezone,
                        )
                        del result_windows[i + 1]
                    elif merge_with_range:
                        result_windows[i] = PersistedTimeWindow.from_public_time_window(
                            TimeWindow(included_window.start, window.end),
                            self.partitions_def.timezone,
                        )
                    elif merge_with_later_range:
                        result_windows[i + 1] = PersistedTimeWindow.from_public_time_window(
                            TimeWindow(window.start, result_windows[i + 1].end),
                            self.partitions_def.timezone,
                        )
                    else:
                        result_windows.insert(
                            i + 1,
                            PersistedTimeWindow.from_public_time_window(
                                window, self.partitions_def.timezone
                            ),
                        )

                    num_added_partitions += 1
                    break
            else:
                if result_windows and window_start_timestamp == result_windows[0].start_timestamp:
                    result_windows[0] = PersistedTimeWindow.from_public_time_window(
                        TimeWindow(window.start, included_window.end),  # pyright: ignore[reportPossiblyUnboundVariable]
                        self.partitions_def.timezone,
                    )
                elif result_windows and window.end.timestamp() == result_windows[0].start_timestamp:
                    result_windows[0] = PersistedTimeWindow.from_public_time_window(
                        TimeWindow(window.start, included_window.end),  # pyright: ignore[reportPossiblyUnboundVariable]
                        self.partitions_def.timezone,
                    )
                else:
                    result_windows.insert(
                        0,
                        PersistedTimeWindow.from_public_time_window(
                            window,
                            self.partitions_def.timezone,
                        ),
                    )

                num_added_partitions += 1

        return result_windows, num_added_partitions

    @public
    def get_partition_keys(self) -> Iterable[str]:
        return [
            pk
            for time_window in self.included_time_windows
            for pk in self.partitions_def.get_partition_keys_in_time_window(time_window)
        ]

    def with_partition_keys(
        self, partition_keys: Iterable[str], validate: bool = True
    ) -> "TimeWindowPartitionsSubset":
        result_windows, added_partitions = self._add_partitions_to_time_windows(
            self.included_time_windows, list(partition_keys), validate=validate
        )

        return TimeWindowPartitionsSubset(
            self.partitions_def,
            num_partitions=self.num_partitions + added_partitions,
            included_time_windows=result_windows,
        )

    def empty_subset(self):
        return self.partitions_def.empty_subset()

    @classmethod
    def create_empty_subset(
        cls, partitions_def: Optional[PartitionsDefinition] = None
    ) -> "PartitionsSubset":
        if not isinstance(partitions_def, TimeWindowPartitionsDefinition):
            check.failed("Partitions definition must be a TimeWindowPartitionsDefinition")
        partitions_def = cast("TimeWindowPartitionsDefinition", partitions_def)
        return cls(partitions_def, 0, [])

    def with_partitions_def(
        self, partitions_def: TimeWindowPartitionsDefinition
    ) -> "TimeWindowPartitionsSubset":
        check.invariant(
            partitions_def.cron_schedule == self.partitions_def.cron_schedule,
            "num_partitions would become inaccurate if the partitions_defs had different cron"
            " schedules",
        )
        return TimeWindowPartitionsSubset(
            partitions_def=partitions_def,
            num_partitions=self.num_partitions,
            included_time_windows=self.included_time_windows,
        )

    def __repr__(self) -> str:
        return f"TimeWindowPartitionsSubset({self.get_partition_key_ranges(self.partitions_def, respect_bounds=False)})"

    def __and__(self, other: "PartitionsSubset") -> "PartitionsSubset":
        other = _attempt_coerce_to_time_window_subset(other)
        if not isinstance(other, TimeWindowPartitionsSubset):
            return super().__and__(other)

        self_time_windows_iter = iter(
            sorted(self.included_time_windows, key=lambda tw: tw.start_timestamp)
        )
        other_time_windows_iter = iter(
            sorted(other.included_time_windows, key=lambda tw: tw.start_timestamp)
        )

        result_windows = []
        self_window = next(self_time_windows_iter, None)
        other_window = next(other_time_windows_iter, None)
        while self_window and other_window:
            # find the intersection between the current two windows
            start_timestamp = max(self_window.start_timestamp, other_window.start_timestamp)
            end_timestamp = min(self_window.end_timestamp, other_window.end_timestamp)

            # these windows intersect
            if start_timestamp < end_timestamp:
                result_windows.append(
                    PersistedTimeWindow(
                        TimestampWithTimezone(start_timestamp, self.partitions_def.timezone),
                        TimestampWithTimezone(end_timestamp, self.partitions_def.timezone),
                    )
                )

            # advance the iterator with the earliest end time to find the next potential intersection
            if self_window.end_timestamp < other_window.end_timestamp:
                self_window = next(self_time_windows_iter, None)
            else:
                other_window = next(other_time_windows_iter, None)

        return TimeWindowPartitionsSubset(
            partitions_def=self.partitions_def,
            num_partitions=None,  # lazily calculated
            included_time_windows=result_windows,
        )

    def __or__(self, other: "PartitionsSubset") -> "PartitionsSubset":
        other = _attempt_coerce_to_time_window_subset(other)
        if not isinstance(other, TimeWindowPartitionsSubset):
            return super().__or__(other)

        input_time_windows = sorted(
            [*self.included_time_windows, *other.included_time_windows],
            key=lambda tw: tw.start_timestamp,
        )
        result_windows = [input_time_windows[0]] if len(input_time_windows) > 0 else []
        for window in input_time_windows[1:]:
            latest_window = result_windows[-1]
            if window.start_timestamp <= latest_window.end_timestamp:
                # merge this window with the latest window
                result_windows[-1] = PersistedTimeWindow.from_public_time_window(
                    TimeWindow(latest_window.start, max(latest_window.end, window.end)),
                    self.partitions_def.timezone,
                )
            else:
                result_windows.append(window)

        return TimeWindowPartitionsSubset(
            partitions_def=self.partitions_def,
            num_partitions=None,  # lazily calculated
            included_time_windows=result_windows,
        )

    def __sub__(self, other: "PartitionsSubset") -> "PartitionsSubset":
        other = _attempt_coerce_to_time_window_subset(other)
        if not isinstance(other, TimeWindowPartitionsSubset):
            return super().__sub__(other)

        time_windows = sorted(self.included_time_windows, key=lambda tw: tw.start_timestamp)
        other_time_windows = sorted(other.included_time_windows, key=lambda tw: tw.start_timestamp)

        next_time_window_index_to_process = 0
        next_other_window_index_to_process = 0

        # Slide through both sets of windows, moving to the next window once its start has passed
        # the end of the window is it being compared to
        while (next_time_window_index_to_process < len(time_windows)) and (
            next_other_window_index_to_process < len(other_time_windows)
        ):
            time_window = time_windows[next_time_window_index_to_process]
            other_time_window = other_time_windows[next_other_window_index_to_process]

            # Perform the subtraction and splice the 0, 1, or 2 result windows
            # back into the time_windows list

            subtracted_time_windows = time_window.subtract(other_time_window)

            time_windows[
                next_time_window_index_to_process : next_time_window_index_to_process + 1
            ] = subtracted_time_windows

            if len(subtracted_time_windows) == 0:
                # other_time_window fully consumed time_window
                # next_time_window_index_to_process can stay the same since everything has shifted over one
                pass
            else:
                updated_time_window = time_windows[next_time_window_index_to_process]
                if updated_time_window.end_timestamp <= other_time_window.start_timestamp:
                    # Current subtractor is too early to intersect, can advance
                    next_time_window_index_to_process += 1
                elif other_time_window.end_timestamp <= updated_time_window.start_timestamp:
                    # current subtractee is too early to intersect, can advance
                    next_other_window_index_to_process += 1
                else:
                    check.failed(
                        "After subtraction, the new window should no longer intersect with the other window"
                    )

        return TimeWindowPartitionsSubset(
            partitions_def=self.partitions_def,
            num_partitions=None,
            included_time_windows=time_windows,
        )

    def __contains__(self, partition_key: Optional[str]) -> bool:  # pyright: ignore[reportIncompatibleMethodOverride]
        if partition_key is None:
            return False

        try:
            time_window = cast(
                "TimeWindowPartitionsDefinition", self.partitions_def
            ).time_window_for_partition_key(partition_key)
        except ValueError:
            # invalid partition key
            return False

        time_window_start_timestamp = time_window.start.timestamp()

        return any(
            time_window_start_timestamp >= included_time_window.start_timestamp
            and time_window_start_timestamp < included_time_window.end_timestamp
            for included_time_window in self.included_time_windows
        )

    def __len__(self) -> int:
        return self.num_partitions

    def __eq__(self, other) -> bool:
        return (
            isinstance(other, TimeWindowPartitionsSubset)
            and self.partitions_def == other.partitions_def
            and self.included_time_windows == other.included_time_windows
        )

    def to_serializable_subset(self) -> "TimeWindowPartitionsSubset":
        from dagster._core.definitions.partitions.snap import TimeWindowPartitionsSnap

        # in cases where we're dealing with (e.g.) HourlyPartitionsDefinition, we need to convert
        # this partitions definition into a raw TimeWindowPartitionsDefinition to make it
        # serializable. to do this, we just convert it to its external representation and back.
        # note that we rarely serialize subsets on the user code side of a serialization boundary,
        # and so this conversion is rarely necessary.
        partitions_def = self.partitions_def
        if type(self.partitions_def) != TimeWindowPartitionsSubset:
            partitions_def = TimeWindowPartitionsSnap.from_def(
                partitions_def
            ).get_partitions_definition()
            return self.with_partitions_def(partitions_def)
        return self

    def serialize(self) -> str:
        return json.dumps(
            {
                "version": self.SERIALIZATION_VERSION,
                # included_time_windows is already sorted, so no need to sort here to guarantee
                # stable serialization between identical subsets
                "time_windows": [
                    (window.start_timestamp, window.end_timestamp)
                    for window in self.included_time_windows
                ],
                "num_partitions": self.num_partitions,
            }
        )

    @classmethod
    def from_serialized(
        cls, partitions_def: PartitionsDefinition, serialized: str
    ) -> "PartitionsSubset":
        if not isinstance(partitions_def, TimeWindowPartitionsDefinition):
            check.failed("Partitions definition must be a TimeWindowPartitionsDefinition")
        partitions_def = cast("TimeWindowPartitionsDefinition", partitions_def)

        loaded = json.loads(serialized)

        def tuples_to_time_windows(tuples):
            return [
                PersistedTimeWindow(
                    TimestampWithTimezone(tup[0], partitions_def.timezone),
                    TimestampWithTimezone(tup[1], partitions_def.timezone),
                )
                for tup in tuples
            ]

        if isinstance(loaded, list):
            # backwards compatibility
            time_windows = tuples_to_time_windows(loaded)
            num_partitions = sum(
                len(partitions_def.get_partition_keys_in_time_window(time_window))
                for time_window in time_windows
            )
        elif isinstance(loaded, dict) and (
            "version" not in loaded or loaded["version"] == cls.SERIALIZATION_VERSION
        ):  # version 1
            time_windows = tuples_to_time_windows(loaded["time_windows"])
            num_partitions = loaded["num_partitions"]
        else:
            raise DagsterInvalidDeserializationVersionError(
                f"Attempted to deserialize partition subset with version {loaded.get('version')},"
                f" but only version {cls.SERIALIZATION_VERSION} is supported."
            )

        return TimeWindowPartitionsSubset(
            partitions_def, num_partitions=num_partitions, included_time_windows=time_windows
        )

    @classmethod
    def can_deserialize(
        cls,
        partitions_def: PartitionsDefinition,
        serialized: str,
        serialized_partitions_def_unique_id: Optional[str],
        serialized_partitions_def_class_name: Optional[str],
    ) -> bool:
        if serialized_partitions_def_unique_id:
            return (
                partitions_def.get_serializable_unique_identifier()
                == serialized_partitions_def_unique_id
            )

        if (
            serialized_partitions_def_class_name
            # note: all TimeWindowPartitionsDefinition subclasses will get serialized as raw
            # TimeWindowPartitionsDefinitions, so this class name check will not always pass,
            # hence the unique id check above
            and serialized_partitions_def_class_name != partitions_def.__class__.__name__
        ):
            return False

        data = json.loads(serialized)
        return isinstance(data, list) or (
            isinstance(data, dict)
            and data.get("time_windows") is not None
            and data.get("num_partitions") is not None
        )
