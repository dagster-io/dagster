from datetime import datetime

import pendulum
from dagster import (
    Definitions,
    _check as check,
    asset,
)
from dagster._core.asset_graph_view.asset_graph_view import AssetGraphView, AssetSlice
from dagster._core.definitions.partition import StaticPartitionsDefinition
from dagster._core.definitions.time_window_partitions import DailyPartitionsDefinition, TimeWindow
from dagster._core.instance import DagsterInstance


def _tw(asset_slice: AssetSlice) -> TimeWindow:
    tws = asset_slice.time_windows
    check.invariant(len(tws) == 1)
    return next(iter(tws))


def test_latest_time_slice_no_end() -> None:
    # starts at 2020-02-01
    no_end_daily = DailyPartitionsDefinition(pendulum.datetime(2020, 2, 1))

    @asset(partitions_def=no_end_daily)
    def daily() -> None: ...

    partition_key_list = [
        "2020-02-01",
        "2020-02-02",
        "2020-02-03",
    ]

    defs = Definitions([daily])
    instance = DagsterInstance.ephemeral()

    # effective date is 2020-2-4

    asset_graph_view_on_2_4 = AssetGraphView.for_test(
        defs, instance, effective_dt=pendulum.datetime(2020, 2, 4)
    )

    assert asset_graph_view_on_2_4.get_asset_slice(daily.key).compute_partition_keys() == set(
        partition_key_list
    )

    assert asset_graph_view_on_2_4.create_latest_time_window_slice(
        daily.key
    ).compute_partition_keys() == {"2020-02-03"}

    assert _tw(
        asset_graph_view_on_2_4.create_latest_time_window_slice(daily.key)
    ).start == pendulum.datetime(2020, 2, 3)

    assert _tw(
        asset_graph_view_on_2_4.create_latest_time_window_slice(daily.key)
    ).end == pendulum.datetime(2020, 2, 4)

    # effective date is 2020-2-5. Ensure one more date

    asset_graph_view_on_2_5 = AssetGraphView.for_test(
        defs, instance, effective_dt=pendulum.datetime(2020, 2, 5)
    )

    assert asset_graph_view_on_2_5.get_asset_slice(daily.key).compute_partition_keys() == set(
        partition_key_list + ["2020-02-04"]
    )

    assert asset_graph_view_on_2_5.create_latest_time_window_slice(
        daily.key
    ).compute_partition_keys() == {"2020-02-04"}

    # in the past

    asset_graph_view_on_1_1 = AssetGraphView.for_test(
        defs, instance, effective_dt=pendulum.datetime(2020, 1, 1)
    )

    assert asset_graph_view_on_1_1.get_asset_slice(daily.key).compute_partition_keys() == set()

    assert (
        asset_graph_view_on_1_1.create_latest_time_window_slice(daily.key).compute_partition_keys()
        == set()
    )

    assert asset_graph_view_on_1_1.create_latest_time_window_slice(daily.key).is_empty

    # effective datetime is in the middle of 02-02, it means the latest
    # complete time window is 02-01 -> 02-02, so the partition key should be 02-01

    asset_graph_view_on_2_2_plus_1_min = AssetGraphView.for_test(
        defs, instance, effective_dt=pendulum.datetime(2020, 2, 2, minute=1)
    )
    assert asset_graph_view_on_2_2_plus_1_min.get_asset_slice(
        daily.key
    ).compute_partition_keys() == set(["2020-02-01"])

    tw = _tw(asset_graph_view_on_2_2_plus_1_min.get_asset_slice(daily.key))

    assert tw.start == datetime.min
    assert tw.end == pendulum.datetime(2020, 2, 2)


def test_latest_time_slice_with_end() -> None:
    # starts at 2020-02-01
    daily_partitions_def = DailyPartitionsDefinition(
        start_date=pendulum.datetime(2020, 1, 1), end_date=pendulum.datetime(2020, 2, 1)
    )

    @asset(partitions_def=daily_partitions_def)
    def daily() -> None: ...

    defs = Definitions([daily])
    instance = DagsterInstance.ephemeral()

    asset_graph_view_before_start = AssetGraphView.for_test(
        defs, instance, effective_dt=pendulum.datetime(2019, 12, 31)
    )
    assert (
        asset_graph_view_before_start.create_latest_time_window_slice(
            daily.key
        ).compute_partition_keys()
        == set()
    )

    asset_graph_view_at_start = AssetGraphView.for_test(
        defs, instance, effective_dt=pendulum.datetime(2020, 1, 1)
    )
    assert (
        asset_graph_view_at_start.create_latest_time_window_slice(
            daily.key
        ).compute_partition_keys()
        == set()
    )

    asset_graph_view_after_start_before_end = AssetGraphView.for_test(
        defs, instance, effective_dt=pendulum.datetime(2020, 1, 3)
    )
    assert asset_graph_view_after_start_before_end.create_latest_time_window_slice(
        daily.key
    ).compute_partition_keys() == set(["2020-01-02"])

    asset_graph_view_after_end = AssetGraphView.for_test(
        defs, instance, effective_dt=pendulum.datetime(2020, 2, 5)
    )
    assert asset_graph_view_after_end.create_latest_time_window_slice(
        daily.key
    ).compute_partition_keys() == set(["2020-01-31"])


def test_latest_time_slice_unpartitioned() -> None:
    @asset
    def unpartitioned() -> None: ...

    defs = Definitions([unpartitioned])
    instance = DagsterInstance.ephemeral()

    asset_graph_view = AssetGraphView.for_test(defs, instance)
    assert not asset_graph_view.get_asset_slice(unpartitioned.key).is_empty
    assert not asset_graph_view.create_latest_time_window_slice(unpartitioned.key).is_empty


def test_latest_time_slice_static_partitioned() -> None:
    number_keys = {"1", "2", "3"}
    number_static_partitions_def = StaticPartitionsDefinition(list(number_keys))

    @asset(partitions_def=number_static_partitions_def)
    def up_numbers() -> None: ...

    defs = Definitions([up_numbers])
    instance = DagsterInstance.ephemeral()

    asset_graph_view = AssetGraphView.for_test(defs, instance)
    latest_up_slice = asset_graph_view.create_latest_time_window_slice(up_numbers.key)
    assert latest_up_slice.compute_partition_keys() == number_keys
