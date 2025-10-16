from typing import cast
from unittest.mock import MagicMock

import dagster as dg
import pytest
from dagster._check import CheckError
from dagster._core.definitions.assets.graph.asset_graph_subset import AssetGraphSubset
from dagster._core.definitions.partitions.context import partition_loading_context
from dagster._core.definitions.partitions.definition import (
    DailyPartitionsDefinition,
    MultiPartitionsDefinition,
    StaticPartitionsDefinition,
)
from dagster._core.definitions.partitions.snap import PartitionsSnap
from dagster._core.definitions.partitions.subset import (
    AllPartitionsSubset,
    DefaultPartitionsSubset,
    KeyRangesPartitionsSubset,
    TimeWindowPartitionsSubset,
)
from dagster._core.definitions.partitions.utils import PersistedTimeWindow
from dagster._core.errors import DagsterInvalidDeserializationVersionError
from dagster._core.test_utils import freeze_time, instance_for_test
from dagster._serdes import deserialize_value, serialize_value
from dagster._time import create_datetime, get_current_datetime


def test_default_subset():
    default_subset = DefaultPartitionsSubset({"a", "b", "c"})
    assert not default_subset.is_empty

    other_default_subset = DefaultPartitionsSubset({"b", "c", "d"})

    empty_subset = DefaultPartitionsSubset(set())
    assert empty_subset.is_empty

    assert default_subset & other_default_subset == DefaultPartitionsSubset({"b", "c"})
    assert default_subset | other_default_subset == DefaultPartitionsSubset({"a", "b", "c", "d"})
    assert default_subset - other_default_subset == DefaultPartitionsSubset({"a"})
    assert other_default_subset - default_subset == DefaultPartitionsSubset({"d"})

    assert default_subset - default_subset == empty_subset
    assert default_subset - empty_subset == default_subset
    assert empty_subset - default_subset == empty_subset

    assert default_subset | default_subset == default_subset
    assert default_subset | empty_subset == default_subset
    assert empty_subset | default_subset == default_subset
    assert default_subset & default_subset == default_subset
    assert default_subset & empty_subset == empty_subset
    assert empty_subset & default_subset == empty_subset


def test_default_subset_cannot_deserialize_invalid_version():
    static_partitions_def = dg.StaticPartitionsDefinition(["a", "b", "c", "d"])
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
    partitions = dg.StaticPartitionsDefinition(["foo", "bar", "baz", "qux"])
    serialization = '["baz", "foo"]'

    deserialized = partitions.deserialize_subset(serialization)
    assert deserialized.get_partition_keys() == {"baz", "foo"}


def test_static_partitions_subset_current_version_serialization():
    partitions = dg.StaticPartitionsDefinition(["foo", "bar", "baz", "qux"])
    serialization = partitions.empty_subset().with_partition_keys(["foo", "baz"]).serialize()
    deserialized = partitions.deserialize_subset(serialization)
    assert deserialized.get_partition_keys() == {"baz", "foo"}

    serialization = '{"version": 1, "subset": ["foo", "baz"]}'
    deserialized = partitions.deserialize_subset(serialization)
    assert deserialized.get_partition_keys() == {"baz", "foo"}


def test_time_window_subset_cannot_deserialize_invalid_version():
    daily_partitions_def = dg.DailyPartitionsDefinition(start_date="2023-01-01")
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


time_window_partitions = dg.DailyPartitionsDefinition(start_date="2021-05-05")
static_partitions = dg.StaticPartitionsDefinition(["a", "b", "c"])
composite = dg.MultiPartitionsDefinition({"date": time_window_partitions, "abc": static_partitions})


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
        (dg.DailyPartitionsDefinition("2023-01-01", timezone="America/New_York")),
        (dg.DailyPartitionsDefinition("2023-01-01")),
    ],
)
def test_time_window_partitions_subset_serialization_deserialization(
    partitions_def: DailyPartitionsDefinition,
):
    time_window_partitions_def = dg.TimeWindowPartitionsDefinition(
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

    deserialized = dg.deserialize_value(
        dg.serialize_value(cast("TimeWindowPartitionsSubset", subset)), TimeWindowPartitionsSubset
    )
    assert deserialized == subset
    assert deserialized.get_partition_keys() == ["2023-01-01"]
    assert (
        deserialized.included_time_windows[0].start.tzinfo
        == subset.included_time_windows[0].start.tzinfo
    )


def test_time_window_partitions_subset_num_partitions_serialization():
    daily_partitions_def = dg.DailyPartitionsDefinition("2023-01-01")
    time_partitions_def = dg.TimeWindowPartitionsDefinition(
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
    deserialized = dg.deserialize_value(dg.serialize_value(subset), TimeWindowPartitionsSubset)
    assert deserialized._asdict()["num_partitions"] is not None


def test_all_partitions_subset_static_partitions_def() -> None:
    static_partitions_def = StaticPartitionsDefinition(["a", "b", "c", "d"])
    with partition_loading_context(dynamic_partitions_store=MagicMock()) as ctx:
        all_subset = AllPartitionsSubset(static_partitions_def, ctx)
        assert len(all_subset) == 4
        assert set(all_subset.get_partition_keys()) == {"a", "b", "c", "d"}
        assert all_subset == AllPartitionsSubset(static_partitions_def, ctx)

        abc_subset = DefaultPartitionsSubset({"a", "b", "c"})
        assert all_subset & abc_subset == abc_subset
        assert all_subset | abc_subset == all_subset
        assert all_subset - abc_subset == DefaultPartitionsSubset({"d"})
        assert abc_subset - all_subset == DefaultPartitionsSubset(set())

        round_trip_subset = deserialize_value(serialize_value(all_subset.to_serializable_subset()))  # type: ignore
        assert isinstance(round_trip_subset, DefaultPartitionsSubset)
        assert set(round_trip_subset.get_partition_keys()) == set(all_subset.get_partition_keys())


def test_all_partitions_subset_time_window_partitions_def() -> None:
    with (
        freeze_time(create_datetime(2020, 1, 6, hour=10)),
        partition_loading_context(dynamic_partitions_store=MagicMock()) as ctx,
    ):
        time_window_partitions_def = DailyPartitionsDefinition(start_date="2020-01-01")
        all_subset = AllPartitionsSubset(time_window_partitions_def, ctx)
        assert len(all_subset) == 5
        assert set(all_subset.get_partition_keys()) == {
            "2020-01-01",
            "2020-01-02",
            "2020-01-03",
            "2020-01-04",
            "2020-01-05",
        }
        assert all_subset == AllPartitionsSubset(time_window_partitions_def, ctx)

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
    static_partitions_def = dg.StaticPartitionsDefinition(["a", "b", "c", "d"])
    default_ps = DefaultPartitionsSubset({"a", "b", "c"})

    with partition_loading_context(dynamic_partitions_store=MagicMock()) as ctx:
        all_ps = AllPartitionsSubset(static_partitions_def, ctx)

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
    color_partition = dg.StaticPartitionsDefinition(["red", "yellow", "blue"])
    number_partition = dg.StaticPartitionsDefinition(["1", "2", "3", "4"])
    multi_partitions_def = dg.MultiPartitionsDefinition(
        {
            "color": color_partition,
            "number": number_partition,
        }
    )
    target_partitions = [
        dg.MultiPartitionKey({"number": "1", "color": "red"}),
        dg.MultiPartitionKey({"number": "2", "color": "red"}),
        dg.MultiPartitionKey({"number": "4", "color": "red"}),
        dg.MultiPartitionKey({"number": "1", "color": "blue"}),
        dg.MultiPartitionKey({"number": "2", "color": "blue"}),
        dg.MultiPartitionKey({"number": "1", "color": "yellow"}),
        dg.MultiPartitionKey({"number": "2", "color": "yellow"}),
        dg.MultiPartitionKey({"number": "3", "color": "yellow"}),
    ]
    # getting ranges from subsets for a multi partition definition contructs ranges for each
    # key of the dimension with the fewest unique values
    expected_ranges = [
        dg.PartitionKeyRange(
            start=dg.MultiPartitionKey({"color": "red", "number": "1"}),
            end=dg.MultiPartitionKey({"color": "red", "number": "2"}),
        ),
        dg.PartitionKeyRange(
            start=dg.MultiPartitionKey({"color": "red", "number": "4"}),
            end=dg.MultiPartitionKey({"color": "red", "number": "4"}),
        ),
        dg.PartitionKeyRange(
            start=dg.MultiPartitionKey({"color": "blue", "number": "1"}),
            end=dg.MultiPartitionKey({"color": "blue", "number": "2"}),
        ),
        dg.PartitionKeyRange(
            start=dg.MultiPartitionKey({"color": "yellow", "number": "1"}),
            end=dg.MultiPartitionKey({"color": "yellow", "number": "3"}),
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


def test_key_ranges_subset():
    color_partition = dg.StaticPartitionsDefinition(
        ["red", "yellow", "blue", "green", "purple", "orange"]
    )

    key_ranges_subset = KeyRangesPartitionsSubset(
        key_ranges=[
            dg.PartitionKeyRange("red", "blue"),
            dg.PartitionKeyRange("orange", "orange"),
        ],
        partitions_snap=PartitionsSnap.from_def(color_partition),
    )

    with pytest.raises(
        CheckError, match="This function can only be called within a partition_loading_context"
    ):
        key_ranges_subset.get_partition_keys()

    assert not key_ranges_subset.is_empty

    with (
        instance_for_test() as instance,
        partition_loading_context(
            effective_dt=get_current_datetime(), dynamic_partitions_store=instance
        ),
    ):
        assert key_ranges_subset.get_partition_keys_not_in_subset(color_partition) == [
            "green",
            "purple",
        ]
        assert not key_ranges_subset.is_empty
        assert key_ranges_subset.partitions_definition == color_partition

        assert key_ranges_subset.get_partition_key_ranges(color_partition) == [
            dg.PartitionKeyRange("red", "blue"),
            dg.PartitionKeyRange("orange", "orange"),
        ]

        assert key_ranges_subset.get_partition_keys() == ["red", "yellow", "blue", "orange"]

        assert key_ranges_subset.with_partition_keys(["green"]) == DefaultPartitionsSubset(
            {"red", "yellow", "blue", "green", "orange"}
        )

        assert KeyRangesPartitionsSubset.can_deserialize(
            color_partition, key_ranges_subset.serialize(), None, None
        )

        assert (
            KeyRangesPartitionsSubset.from_serialized(
                color_partition, key_ranges_subset.serialize()
            )
            == key_ranges_subset
        )

        assert "yellow" in key_ranges_subset
        assert "orange" in key_ranges_subset
        assert "green" not in key_ranges_subset

        assert len(key_ranges_subset) == 4

        empty_subset = KeyRangesPartitionsSubset(
            key_ranges=[], partitions_snap=PartitionsSnap.from_def(color_partition)
        )

        assert empty_subset == key_ranges_subset.empty_subset()
        assert empty_subset == KeyRangesPartitionsSubset.create_empty_subset(color_partition)

        assert len(empty_subset) == 0
        assert empty_subset.is_empty
        assert empty_subset.partitions_definition == color_partition
        assert empty_subset.get_partition_keys() == []
        assert empty_subset.get_partition_key_ranges(color_partition) == []
        assert empty_subset.with_partition_keys(["red"]) == DefaultPartitionsSubset({"red"})


def test_key_ranges_subset_dynamic_partitions():
    dynamic_partitions_def = dg.DynamicPartitionsDefinition(name="dynamic_partitions_def")
    with instance_for_test() as instance:
        instance.add_dynamic_partitions("dynamic_partitions_def", ["a", "b", "c", "d"])
        key_ranges_subset = KeyRangesPartitionsSubset(
            key_ranges=[dg.PartitionKeyRange("a", "c")],
            partitions_snap=PartitionsSnap.from_def(dynamic_partitions_def),
        )
        with pytest.raises(CheckError):
            key_ranges_subset.get_partition_keys()

        with partition_loading_context(dynamic_partitions_store=instance):
            assert key_ranges_subset.get_partition_keys() == ["a", "b", "c"]

        asset_graph_subset = AssetGraphSubset(
            partitions_subsets_by_asset_key={
                dg.AssetKey("asset"): key_ranges_subset,
            },
            non_partitioned_asset_keys=set(),
        )

        # can get asset keys from subset without partition loading context
        assert asset_graph_subset.asset_keys == {dg.AssetKey("asset")}


def test_multi_partition_subset_to_range_conversion_grouping_choices():
    # Test that converting from a list of partitions keys to a subset, to a list of ranges, and back to
    # a list of partition keys for MultiPartitionsDefinitions does not lose any partitions.
    color_partition = dg.StaticPartitionsDefinition(["red", "yellow", "blue"])
    number_partition = dg.StaticPartitionsDefinition(["1", "2", "3", "4"])
    multi_partitions_def = dg.MultiPartitionsDefinition(
        {
            "color": color_partition,
            "number": number_partition,
        }
    )

    # we expect the grouping to happen by the dimension with the fewest unique values
    # in this case number
    group_by_number_target_partitions = [
        dg.MultiPartitionKey({"number": "1", "color": "red"}),
        dg.MultiPartitionKey({"number": "1", "color": "yellow"}),
        dg.MultiPartitionKey({"number": "1", "color": "blue"}),
    ]
    # getting ranges from subsets for a multi partition definition contructs ranges for each
    # key of the primary dimension
    expected_ranges = [
        dg.PartitionKeyRange(
            start=dg.MultiPartitionKey({"color": "red", "number": "1"}),
            end=dg.MultiPartitionKey({"color": "blue", "number": "1"}),
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
        dg.MultiPartitionKey({"number": "1", "color": "red"}),
        dg.MultiPartitionKey({"number": "2", "color": "red"}),
        dg.MultiPartitionKey({"number": "3", "color": "red"}),
        dg.MultiPartitionKey({"number": "1", "color": "blue"}),
        dg.MultiPartitionKey({"number": "2", "color": "blue"}),
        dg.MultiPartitionKey({"number": "4", "color": "blue"}),
    ]
    expected_ranges = [
        dg.PartitionKeyRange(
            start=dg.MultiPartitionKey({"color": "red", "number": "1"}),
            end=dg.MultiPartitionKey({"color": "red", "number": "3"}),
        ),
        dg.PartitionKeyRange(
            start=dg.MultiPartitionKey({"color": "blue", "number": "1"}),
            end=dg.MultiPartitionKey({"color": "blue", "number": "2"}),
        ),
        dg.PartitionKeyRange(
            start=dg.MultiPartitionKey({"color": "blue", "number": "4"}),
            end=dg.MultiPartitionKey({"color": "blue", "number": "4"}),
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
    color_partition = dg.StaticPartitionsDefinition(["red", "yellow", "blue"])
    hour_partition = dg.HourlyPartitionsDefinition(
        start_date="2023-01-01-00:00", end_date="2025-01-01-01:00"
    )
    multi_partitions_def = dg.MultiPartitionsDefinition(
        {
            "a_date": hour_partition,  # prefix with a so that it is the primary dimension
            "color": color_partition,
        }
    )

    # we expect the grouping to happen by the dimension with the fewest unique values
    # in this case a_date
    group_by_hour_target_partitions = [
        dg.MultiPartitionKey({"a_date": "2023-01-01-00:00", "color": "red"}),
        dg.MultiPartitionKey({"a_date": "2023-01-01-00:00", "color": "yellow"}),
        dg.MultiPartitionKey({"a_date": "2023-01-01-00:00", "color": "blue"}),
    ]
    # getting ranges from subsets for a multi partition definition contructs ranges for each
    # key of the primary dimension
    expected_ranges = [
        dg.PartitionKeyRange(
            start=dg.MultiPartitionKey({"color": "red", "a_date": "2023-01-01-00:00"}),
            end=dg.MultiPartitionKey({"color": "blue", "a_date": "2023-01-01-00:00"}),
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
        dg.PartitionKeyRange(
            start=dg.MultiPartitionKey({"color": "red", "a_date": "2023-01-01-00:00"}),
            end=dg.MultiPartitionKey({"color": "red", "a_date": "2025-01-01-00:00"}),
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
