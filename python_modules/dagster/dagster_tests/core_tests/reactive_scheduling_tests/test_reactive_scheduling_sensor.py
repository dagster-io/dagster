from typing import Set

import pendulum
from dagster import (
    Definitions,
    asset,
)
from dagster._core.definitions.asset_graph_subset import AssetGraphSubset
from dagster._core.definitions.events import AssetKey
from dagster._core.definitions.run_request import SensorResult
from dagster._core.definitions.sensor_definition import build_sensor_context
from dagster._core.definitions.time_window_partitions import (
    DailyPartitionsDefinition,
    HourlyPartitionsDefinition,
    TimeWindow,
)
from dagster._core.instance import DagsterInstance
from dagster._core.reactive_scheduling.scheduling_policy import SchedulingExecutionContext
from dagster._core.reactive_scheduling.scheduling_sensor import (
    ReactiveSensorCursor,
    SensorSpec,
    pulse_reactive_scheduling,
)
from dagster._serdes.serdes import deserialize_value
from dagster._seven.compat.pendulum import pendulum_freeze_time

from .test_policies import (
    AlwaysIncludeSchedulingPolicy,
    AlwaysLaunchLatestTimeWindowSchedulingPolicy,
    AlwaysLaunchSchedulingPolicy,
    build_test_context,
    slices_equal,
)


def graph_subset_from_keys(
    context: SchedulingExecutionContext, asset_keys: Set[AssetKey]
) -> AssetGraphSubset:
    return AssetGraphSubset.from_asset_keys(
        asset_keys=asset_keys,
        asset_graph=context.asset_graph,
        dynamic_partitions_store=context.queryer,
        current_time=context.tick_dt,
    )


def test_shared_sensor_spec() -> None:
    sensor_spec = SensorSpec(name="test_sensor", description="test_description")

    @asset(scheduling_policy=AlwaysLaunchSchedulingPolicy(sensor_spec))
    def launchy_asset_1() -> None:
        ...

    @asset(scheduling_policy=AlwaysLaunchSchedulingPolicy(sensor_spec))
    def launchy_asset_2() -> None:
        ...

    defs = Definitions([launchy_asset_1, launchy_asset_2])

    assert defs.get_sensor_def("test_sensor")
    assert defs.get_sensor_def("test_sensor").description == "test_description"

    sensor_def = defs.get_sensor_def("test_sensor")

    instance = DagsterInstance.ephemeral()

    dt = pendulum.datetime(2020, 1, 1)

    with pendulum_freeze_time(dt):
        sensor_context = build_sensor_context(
            instance=instance, repository_def=defs.get_repository_def()
        )

        result = sensor_def(context=sensor_context)

    assert isinstance(result, SensorResult)
    assert isinstance(result.cursor, str)
    cursor = deserialize_value(result.cursor, as_type=ReactiveSensorCursor)
    assert cursor.tick_dt == dt

    context = build_test_context(defs, instance=instance, tick_dt=dt)

    plan1 = pulse_reactive_scheduling(context, {launchy_asset_1.key})

    assert plan1.launch_partition_space.asset_keys == {launchy_asset_1.key}

    plan2 = pulse_reactive_scheduling(context, {launchy_asset_2.key})

    assert plan2.launch_partition_space.asset_keys == {launchy_asset_2.key}

    plan12 = pulse_reactive_scheduling(context, {launchy_asset_1.key, launchy_asset_2.key})

    assert plan12.launch_partition_space.asset_keys == {launchy_asset_1.key, launchy_asset_2.key}

    brs = list(result.backfill_requests or [])
    assert len(brs) == 1
    br = brs[0]
    assert br.asset_partitions == graph_subset_from_keys(
        context, {launchy_asset_1.key, launchy_asset_2.key}
    )


def test_daily_to_hourly_upstream() -> None:
    start_date = pendulum.datetime(2024, 1, 1)
    end_date = pendulum.datetime(2024, 2, 1)

    sensor_spec = SensorSpec(name="test_sensor", description="test_description")

    @asset(
        partitions_def=HourlyPartitionsDefinition(start_date=start_date, end_date=end_date),
        scheduling_policy=AlwaysIncludeSchedulingPolicy(),
    )
    def hourly() -> None:
        ...

    @asset(
        deps=[hourly],
        partitions_def=DailyPartitionsDefinition(start_date=start_date, end_date=end_date),
        scheduling_policy=AlwaysLaunchLatestTimeWindowSchedulingPolicy(sensor_spec),
    )
    def daily() -> None:
        ...

    defs = Definitions([hourly, daily])

    assert defs

    tick_dt = pendulum.datetime(2024, 1, 31, 1, 0, 0)

    context = build_test_context(defs, tick_dt=tick_dt)

    plan = pulse_reactive_scheduling(context, {daily.key})

    daily_slice = plan.launch_partition_space.get_asset_slice(daily.key)
    assert daily_slice.has_single_time_window
    assert daily_slice.time_window == TimeWindow(
        pendulum.datetime(2024, 1, 30), pendulum.datetime(2024, 1, 31)
    )

    # latest(1 am at 1/31) => 1/30 daily partition -> 1/30 12 AM - 1/31 12 AM hourly partition
    assert slices_equal(
        plan.launch_partition_space.get_asset_slice(hourly.key),
        context.slice_factory.from_time_window(
            hourly.key,
            time_window=TimeWindow(
                start=pendulum.datetime(2024, 1, 30, 0, 0, 0),
                end=pendulum.datetime(2024, 1, 31, 0, 0, 0),
            ),
        ),
    )
