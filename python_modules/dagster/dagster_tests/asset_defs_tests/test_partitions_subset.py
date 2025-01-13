from typing import cast
from unittest.mock import Mock

import pytest
from dagster import DailyPartitionsDefinition, MultiPartitionsDefinition, StaticPartitionsDefinition
from dagster._core.definitions.partition import AllPartitionsSubset, DefaultPartitionsSubset
from dagster._core.definitions.time_window_partitions import (
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
        TimeWindowPartitionsSubset,
        TimeWindowPartitionsSubset.create_empty_subset(
            time_window_partitions_def
        ).with_partition_keys(["2023-01-01"]),
    )

    deserialized = deserialize_value(
        serialize_value(cast(TimeWindowPartitionsSubset, subset)), TimeWindowPartitionsSubset
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
