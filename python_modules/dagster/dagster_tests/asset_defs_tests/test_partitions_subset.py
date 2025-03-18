from typing import cast
from unittest.mock import Mock

import pytest
from dagster import (
    DailyPartitionsDefinition,
    MultiPartitionKey,
    MultiPartitionsDefinition,
    StaticPartitionsDefinition,
)
from dagster._core.definitions.partition import AllPartitionsSubset, DefaultPartitionsSubset
from dagster._core.definitions.partition_key_range import PartitionKeyRange
from dagster._core.definitions.time_window_partitions import (
    HourlyPartitionsDefinition,
    PersistedTimeWindow,
    TimeWindowPartitionsDefinition,
    TimeWindowPartitionsSubset,
)
from dagster._core.errors import DagsterInvalidDeserializationVersionError
from dagster._core.test_utils import freeze_time
from dagster._serdes import deserialize_value, serialize_value
from dagster._time import create_datetime, get_current_datetime


def test_default_subset_cannot_deserialize_invalid_version():
    static_partitions_def = StaticPartitionsDefinition(["a", "b", "c", "d"])
    serialized_subset = (
        static_partitions_def.empty_subset().with_partition_keys(["a", "c", "d"]).serialize()
    )

    assert static_partitions_def.deserialize_subset(serialized_subset).get_partition_keys() == {
        "a",
        "c",
        "d",
    }

    class NewSerializationVersionSubset(DefaultPartitionsSubset):
        SERIALIZATION_VERSION = -1

    with pytest.raises(DagsterInvalidDeserializationVersionError, match="version -1"):
        NewSerializationVersionSubset.from_serialized(static_partitions_def, serialized_subset)


def test_static_partitions_subset_backwards_compat():
    partitions = StaticPartitionsDefinition(["foo", "bar", "baz", "qux"])
    serialization = '["baz", "foo"]'

    deserialized = partitions.deserialize_subset(serialization)
    assert deserialized.get_partition_keys() == {"baz", "foo"}


def test_static_partitions_subset_current_version_serialization():
    partitions = StaticPartitionsDefinition(["foo", "bar", "baz", "qux"])
    serialization = partitions.empty_subset().with_partition_keys(["foo", "baz"]).serialize()
    deserialized = partitions.deserialize_subset(serialization)
    assert deserialized.get_partition_keys() == {"baz", "foo"}

    serialization = '{"version": 1, "subset": ["foo", "baz"]}'
    deserialized = partitions.deserialize_subset(serialization)
    assert deserialized.get_partition_keys() == {"baz", "foo"}


def test_time_window_subset_cannot_deserialize_invalid_version():
    daily_partitions_def = DailyPartitionsDefinition(start_date="2023-01-01")
    serialized_subset = (
        daily_partitions_def.empty_subset().with_partition_keys(["2023-01-02"]).serialize()
    )

    assert set(daily_partitions_def.deserialize_subset(serialized_subset).get_partition_keys()) == {
        "2023-01-02"
    }

    class NewSerializationVersionSubset(TimeWindowPartitionsSubset):
        SERIALIZATION_VERSION = -2

    with pytest.raises(DagsterInvalidDeserializationVersionError, match="version -2"):
        NewSerializationVersionSubset.from_serialized(daily_partitions_def, serialized_subset)


time_window_partitions = DailyPartitionsDefinition(start_date="2021-05-05")
static_partitions = StaticPartitionsDefinition(["a", "b", "c"])
composite = MultiPartitionsDefinition({"date": time_window_partitions, "abc": static_partitions})


def test_get_subset_type():
    assert composite.__class__.__name__ == MultiPartitionsDefinition.__name__
    assert static_partitions.__class__.__name__ == StaticPartitionsDefinition.__name__
    assert time_window_partitions.__class__.__name__ == DailyPartitionsDefinition.__name__


def test_empty_subsets():
    assert type(static_partitions.empty_subset()) is DefaultPartitionsSubset
    assert type(time_window_partitions.empty_subset()) is TimeWindowPartitionsSubset


@pytest.mark.parametrize(
    "partitions_def",
    [
        (DailyPartitionsDefinition("2023-01-01", timezone="America/New_York")),
        (DailyPartitionsDefinition("2023-01-01")),
    ],
)
def test_time_window_partitions_subset_serialization_deserialization(
    partitions_def: DailyPartitionsDefinition,
):
    time_window_partitions_def = TimeWindowPartitionsDefinition(
        start=partitions_def.start,
        end=partitions_def.end,
        cron_schedule="0 0 * * *",
        fmt="%Y-%m-%d",
        timezone=partitions_def.timezone,
        end_offset=partitions_def.end_offset,
    )
    subset = cast(
        "TimeWindowPartitionsSubset",
        TimeWindowPartitionsSubset.create_empty_subset(
            time_window_partitions_def
        ).with_partition_keys(["2023-01-01"]),
    )

    deserialized = deserialize_value(
        serialize_value(cast("TimeWindowPartitionsSubset", subset)), TimeWindowPartitionsSubset
    )
    assert deserialized == subset
    assert deserialized.get_partition_keys() == ["2023-01-01"]
    assert (
        deserialized.included_time_windows[0].start.tzinfo
        == subset.included_time_windows[0].start.tzinfo
    )


def test_time_window_partitions_subset_num_partitions_serialization():
    daily_partitions_def = DailyPartitionsDefinition("2023-01-01")
    time_partitions_def = TimeWindowPartitionsDefinition(
        start=daily_partitions_def.start,
        end=daily_partitions_def.end,
        cron_schedule="0 0 * * *",
        fmt="%Y-%m-%d",
        timezone=daily_partitions_def.timezone,
        end_offset=daily_partitions_def.end_offset,
    )

    tw = PersistedTimeWindow.from_public_time_window(
        time_partitions_def.time_window_for_partition_key("2023-01-01"),
        time_partitions_def.timezone,
    )

    subset = TimeWindowPartitionsSubset(
        time_partitions_def, num_partitions=None, included_time_windows=[tw]
    )
    deserialized = deserialize_value(serialize_value(subset), TimeWindowPartitionsSubset)
    assert deserialized._asdict()["num_partitions"] is not None


def test_all_partitions_subset_static_partitions_def() -> None:
    static_partitions_def = StaticPartitionsDefinition(["a", "b", "c", "d"])
    all_subset = AllPartitionsSubset(static_partitions_def, Mock(), get_current_datetime())
    assert len(all_subset) == 4
    assert set(all_subset.get_partition_keys()) == {"a", "b", "c", "d"}
    assert all_subset == AllPartitionsSubset(static_partitions_def, Mock(), get_current_datetime())

    abc_subset = DefaultPartitionsSubset({"a", "b", "c"})
    assert all_subset & abc_subset == abc_subset
    assert all_subset | abc_subset == all_subset
    assert all_subset - abc_subset == DefaultPartitionsSubset({"d"})
    assert abc_subset - all_subset == DefaultPartitionsSubset(set())

    round_trip_subset = deserialize_value(serialize_value(all_subset.to_serializable_subset()))  # type: ignore
    assert isinstance(round_trip_subset, DefaultPartitionsSubset)
    assert set(round_trip_subset.get_partition_keys()) == set(all_subset.get_partition_keys())


def test_all_partitions_subset_time_window_partitions_def() -> None:
    with freeze_time(create_datetime(2020, 1, 6, hour=10)):
        time_window_partitions_def = DailyPartitionsDefinition(start_date="2020-01-01")
        all_subset = AllPartitionsSubset(time_window_partitions_def, Mock(), get_current_datetime())
        assert len(all_subset) == 5
        assert set(all_subset.get_partition_keys()) == {
            "2020-01-01",
            "2020-01-02",
            "2020-01-03",
            "2020-01-04",
            "2020-01-05",
        }
        assert all_subset == AllPartitionsSubset(
            time_window_partitions_def, Mock(), get_current_datetime()
        )

        subset = time_window_partitions_def.subset_with_partition_keys(
            {"2020-01-01", "2020-01-02", "2020-01-03"}
        )
        assert all_subset & subset == subset
        assert all_subset | subset == all_subset
        assert all_subset - subset == time_window_partitions_def.subset_with_partition_keys(
            {"2020-01-04", "2020-01-05"}
        )
        assert subset - all_subset == time_window_partitions_def.empty_subset()

        round_trip_subset = deserialize_value(serialize_value(all_subset.to_serializable_subset()))  # type: ignore
        assert isinstance(round_trip_subset, TimeWindowPartitionsSubset)
        assert set(round_trip_subset.get_partition_keys()) == set(all_subset.get_partition_keys())


def test_partitions_set_short_circuiting() -> None:
    static_partitions_def = StaticPartitionsDefinition(["a", "b", "c", "d"])
    default_ps = DefaultPartitionsSubset({"a", "b", "c"})
    all_ps = AllPartitionsSubset(static_partitions_def, Mock(), get_current_datetime())

    # Test short-circuiting of |. Returns the same AllPartionsSubset
    or_result = default_ps | all_ps
    assert or_result is all_ps

    # Test short-circuiting of &. Returns the same DefaultPartitionsSubset
    and_result = default_ps & all_ps
    assert and_result is default_ps

    # Test short-circuiting of -. Returns an empty DefaultPartitionsSubset
    assert (default_ps - all_ps) == DefaultPartitionsSubset.create_empty_subset()


def test_multi_partition_subset_to_range_conversion():
    # Test that converting from a list of partitions keys to a subset, to a list of ranges, and back to
    # a list of partition keys for MultiPartitionsDefinitions does not lose any partitions.
    color_partition = StaticPartitionsDefinition(["red", "yellow", "blue"])
    number_partition = StaticPartitionsDefinition(["1", "2", "3", "4"])
    multi_partitions_def = MultiPartitionsDefinition(
        {
            "color": color_partition,
            "number": number_partition,
        }
    )
    target_partitions = [
        MultiPartitionKey({"number": "1", "color": "red"}),
        MultiPartitionKey({"number": "2", "color": "red"}),
        MultiPartitionKey({"number": "4", "color": "red"}),
        MultiPartitionKey({"number": "1", "color": "blue"}),
        MultiPartitionKey({"number": "2", "color": "blue"}),
        MultiPartitionKey({"number": "1", "color": "yellow"}),
        MultiPartitionKey({"number": "2", "color": "yellow"}),
        MultiPartitionKey({"number": "3", "color": "yellow"}),
    ]
    # getting ranges from subsets for a multi partition definition contructs ranges for each
    # key of the dimension with the fewest unique values
    expected_ranges = [
        PartitionKeyRange(
            start=MultiPartitionKey({"color": "red", "number": "1"}),
            end=MultiPartitionKey({"color": "red", "number": "2"}),
        ),
        PartitionKeyRange(
            start=MultiPartitionKey({"color": "red", "number": "4"}),
            end=MultiPartitionKey({"color": "red", "number": "4"}),
        ),
        PartitionKeyRange(
            start=MultiPartitionKey({"color": "blue", "number": "1"}),
            end=MultiPartitionKey({"color": "blue", "number": "2"}),
        ),
        PartitionKeyRange(
            start=MultiPartitionKey({"color": "yellow", "number": "1"}),
            end=MultiPartitionKey({"color": "yellow", "number": "3"}),
        ),
    ]
    partition_subset = multi_partitions_def.subset_with_partition_keys(target_partitions)
    partition_key_ranges = partition_subset.get_partition_key_ranges(multi_partitions_def)
    assert sorted(partition_key_ranges) == sorted(expected_ranges)

    partition_keys_from_ranges = []
    for partition_key_range in partition_key_ranges:
        partition_keys_from_ranges.extend(
            multi_partitions_def.get_partition_keys_in_range(partition_key_range)
        )
    assert sorted(partition_keys_from_ranges) == sorted(target_partitions)


def test_multi_partition_subset_to_range_conversion_grouping_choices():
    # Test that converting from a list of partitions keys to a subset, to a list of ranges, and back to
    # a list of partition keys for MultiPartitionsDefinitions does not lose any partitions.
    color_partition = StaticPartitionsDefinition(["red", "yellow", "blue"])
    number_partition = StaticPartitionsDefinition(["1", "2", "3", "4"])
    multi_partitions_def = MultiPartitionsDefinition(
        {
            "color": color_partition,
            "number": number_partition,
        }
    )

    # we expect the grouping to happen by the dimension with the fewest unique values
    # in this case number
    group_by_number_target_partitions = [
        MultiPartitionKey({"number": "1", "color": "red"}),
        MultiPartitionKey({"number": "1", "color": "yellow"}),
        MultiPartitionKey({"number": "1", "color": "blue"}),
    ]
    # getting ranges from subsets for a multi partition definition contructs ranges for each
    # key of the primary dimension
    expected_ranges = [
        PartitionKeyRange(
            start=MultiPartitionKey({"color": "red", "number": "1"}),
            end=MultiPartitionKey({"color": "blue", "number": "1"}),
        ),
    ]
    partition_subset = multi_partitions_def.subset_with_partition_keys(
        group_by_number_target_partitions
    )
    partition_key_ranges = partition_subset.get_partition_key_ranges(multi_partitions_def)
    assert sorted(partition_key_ranges) == sorted(expected_ranges)

    partition_keys_from_ranges = []
    for partition_key_range in partition_key_ranges:
        partition_keys_from_ranges.extend(
            multi_partitions_def.get_partition_keys_in_range(partition_key_range)
        )
    assert sorted(partition_keys_from_ranges) == sorted(group_by_number_target_partitions)

    # we expect the grouping to happen by the dimension with the fewest unique values
    # in this case color
    group_by_color_target_partitions = [
        MultiPartitionKey({"number": "1", "color": "red"}),
        MultiPartitionKey({"number": "2", "color": "red"}),
        MultiPartitionKey({"number": "3", "color": "red"}),
        MultiPartitionKey({"number": "1", "color": "blue"}),
        MultiPartitionKey({"number": "2", "color": "blue"}),
        MultiPartitionKey({"number": "4", "color": "blue"}),
    ]
    expected_ranges = [
        PartitionKeyRange(
            start=MultiPartitionKey({"color": "red", "number": "1"}),
            end=MultiPartitionKey({"color": "red", "number": "3"}),
        ),
        PartitionKeyRange(
            start=MultiPartitionKey({"color": "blue", "number": "1"}),
            end=MultiPartitionKey({"color": "blue", "number": "2"}),
        ),
        PartitionKeyRange(
            start=MultiPartitionKey({"color": "blue", "number": "4"}),
            end=MultiPartitionKey({"color": "blue", "number": "4"}),
        ),
    ]
    partition_subset = multi_partitions_def.subset_with_partition_keys(
        group_by_color_target_partitions
    )
    partition_key_ranges = partition_subset.get_partition_key_ranges(multi_partitions_def)
    assert sorted(partition_key_ranges) == sorted(expected_ranges)

    partition_keys_from_ranges = []
    for partition_key_range in partition_key_ranges:
        partition_keys_from_ranges.extend(
            multi_partitions_def.get_partition_keys_in_range(partition_key_range)
        )
    assert sorted(partition_keys_from_ranges) == sorted(group_by_color_target_partitions)


def test_multi_partition_subset_to_range_conversion_time_partition():
    # Test that converting from a list of partitions keys to a subset, to a list of ranges, and back to
    # a list of partition keys for MultiPartitionsDefinitions does not lose any partitions.
    color_partition = StaticPartitionsDefinition(["red", "yellow", "blue"])
    hour_partition = HourlyPartitionsDefinition(
        start_date="2023-01-01-00:00", end_date="2025-01-01-01:00"
    )
    multi_partitions_def = MultiPartitionsDefinition(
        {
            "a_date": hour_partition,  # prefix with a so that it is the primary dimension
            "color": color_partition,
        }
    )

    # we expect the grouping to happen by the dimension with the fewest unique values
    # in this case a_date
    group_by_hour_target_partitions = [
        MultiPartitionKey({"a_date": "2023-01-01-00:00", "color": "red"}),
        MultiPartitionKey({"a_date": "2023-01-01-00:00", "color": "yellow"}),
        MultiPartitionKey({"a_date": "2023-01-01-00:00", "color": "blue"}),
    ]
    # getting ranges from subsets for a multi partition definition contructs ranges for each
    # key of the primary dimension
    expected_ranges = [
        PartitionKeyRange(
            start=MultiPartitionKey({"color": "red", "a_date": "2023-01-01-00:00"}),
            end=MultiPartitionKey({"color": "blue", "a_date": "2023-01-01-00:00"}),
        ),
    ]
    partition_subset = multi_partitions_def.subset_with_partition_keys(
        group_by_hour_target_partitions
    )
    partition_key_ranges = partition_subset.get_partition_key_ranges(multi_partitions_def)
    assert sorted(partition_key_ranges) == sorted(expected_ranges)

    partition_keys_from_ranges = []
    for partition_key_range in partition_key_ranges:
        partition_keys_from_ranges.extend(
            multi_partitions_def.get_partition_keys_in_range(partition_key_range)
        )
    assert sorted(partition_keys_from_ranges) == sorted(group_by_hour_target_partitions)

    # we expect the grouping to happen by the dimension with the fewest unique values
    # in this case color
    group_by_color_target_partitions = (
        multi_partitions_def.get_multipartition_keys_with_dimension_value(
            dimension_name="color", dimension_partition_key="red"
        )
    )
    expected_ranges = [
        PartitionKeyRange(
            start=MultiPartitionKey({"color": "red", "a_date": "2023-01-01-00:00"}),
            end=MultiPartitionKey({"color": "red", "a_date": "2025-01-01-00:00"}),
        ),
    ]
    partition_subset = multi_partitions_def.subset_with_partition_keys(
        group_by_color_target_partitions
    )
    partition_key_ranges = partition_subset.get_partition_key_ranges(multi_partitions_def)
    assert sorted(partition_key_ranges) == sorted(expected_ranges)

    partition_keys_from_ranges = []
    for partition_key_range in partition_key_ranges:
        partition_keys_from_ranges.extend(
            multi_partitions_def.get_partition_keys_in_range(partition_key_range)
        )
    assert sorted(partition_keys_from_ranges) == sorted(group_by_color_target_partitions)
