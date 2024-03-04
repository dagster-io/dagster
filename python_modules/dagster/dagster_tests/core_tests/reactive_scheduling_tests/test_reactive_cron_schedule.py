import pendulum
from dagster import (
    asset,
)
from dagster._core.definitions.definitions_class import Definitions
from dagster._core.instance import DagsterInstance
from dagster._core.reactive_scheduling.asset_graph_view import AssetPartition
from dagster._core.reactive_scheduling.cron import Cron, CronCursor
from dagster._core.reactive_scheduling.scheduling_policy import (
    SchedulingExecutionContext,
)
from dagster._core.reactive_scheduling.scheduling_sensor import SensorSpec


def test_daily_cron_schedule_no_previous_launch() -> None:
    daily_midnight_cron = Cron(
        cron_schedule="0 0 * * *", timezone="UTC", sensor_spec=SensorSpec("test_sensor")
    )

    @asset(scheduling_policy=daily_midnight_cron)
    def daily_scheduled() -> None:
        ...

    defs = Definitions([daily_scheduled])

    # previous_dt = pendulum.datetime(2021, month=1, day=1,minute=1)
    current_dt = pendulum.datetime(2021, month=1, day=2, minute=1)
    context = SchedulingExecutionContext.create(
        instance=DagsterInstance.ephemeral(),
        repository_def=defs.get_repository_def(),
        effective_dt=current_dt,
        last_event_id=None,
        previous_cursor=None,  # no previous launches
    )
    result = daily_midnight_cron.schedule_launch(
        context=context,
        asset_slice=context.asset_graph_view.slice_factory.complete_asset_slice(
            daily_scheduled.key
        ),
    )
    assert result.launch
    assert result.explicit_launching_slice
    assert result.explicit_launching_slice.materialize_asset_partitions() == {
        AssetPartition(daily_scheduled.key)
    }


def test_daily_cron_schedule_previous_launch_in_window() -> None:
    daily_midnight_cron = Cron(
        cron_schedule="0 0 * * *", timezone="UTC", sensor_spec=SensorSpec("test_sensor")
    )

    @asset(scheduling_policy=daily_midnight_cron)
    def daily_scheduled() -> None:
        ...

    defs = Definitions([daily_scheduled])

    previous_dt = pendulum.datetime(2021, month=1, day=1, minute=1)
    effective_dt = pendulum.datetime(2021, month=1, day=1, hour=1, minute=1)

    context = SchedulingExecutionContext.create(
        instance=DagsterInstance.ephemeral(),
        repository_def=defs.get_repository_def(),
        effective_dt=effective_dt,
        last_event_id=None,
        previous_cursor=CronCursor(previous_launch_timestamp=previous_dt.timestamp()).serialize(),
    )

    result = daily_midnight_cron.schedule_launch(
        context=context,
        asset_slice=context.asset_graph_view.slice_factory.complete_asset_slice(
            daily_scheduled.key
        ),
    )
    assert not result.launch


#     previous_dt = datetime.fromisoformat("2021-01-01T00:00:01")
#     # 1 hour after previous_dt
#     previous_launch_dt = datetime.fromisoformat("2021-01-01T00:01:01")
#     # 1 hour after previous_launch_dt
#     current_dt = datetime.fromisoformat("2021-01-01T00:02:01")  #
#     result = cron.schedule(
#         SchedulingExecutionContext(
#             previous_tick_dt=previous_dt,
#             tick_dt=current_dt,
#             repository_def=defs.get_repository_def(),
#             queryer=CachingInstanceQueryer.ephemeral(defs),
#             ticked_asset_key=daily_scheduled.key,
#             previous_cursor=CronCursor(
#                 previous_launch_timestamp=previous_launch_dt.timestamp()
#             ).serialize(),
#         )
#     )
#     assert not result.launch
#     assert result.explicit_partition_range is None
