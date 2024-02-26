from datetime import datetime

from dagster import (
    asset,
)
from dagster._core.definitions.definitions_class import Definitions
from dagster._core.instance import DagsterInstance
from dagster._core.reactive_scheduling.cron_ticker import Cron, CronCursor
from dagster._core.reactive_scheduling.scheduling_policy import (
    SchedulingExecutionContext,
)


def test_daily_cron_schedule_no_previous_launch() -> None:
    scheduling_policy = Cron(cron_schedule="0 0 * * *")

    @asset(scheduling_policy=scheduling_policy)
    def daily_scheduled() -> None:
        ...

    defs = Definitions([daily_scheduled])
    cron = Cron(cron_schedule="0 0 * * *")
    previous_dt = datetime.fromisoformat("2021-01-01T00:00:01")
    current_dt = datetime.fromisoformat("2021-01-02T00:00:01")
    result = cron.schedule(
        SchedulingExecutionContext(
            previous_tick_dt=previous_dt,
            tick_dt=current_dt,
            repository_def=defs.get_repository_def(),
            instance=DagsterInstance.ephemeral(),
            asset_key=daily_scheduled.key,
            # no previous launches
            previous_cursor=None,
        )
    )
    assert result.launch
    assert result.partition_keys is None


def test_daily_cron_schedule_previous_launch_in_window() -> None:
    scheduling_policy = Cron(cron_schedule="0 0 * * *")

    @asset(scheduling_policy=scheduling_policy)
    def daily_scheduled() -> None:
        ...

    defs = Definitions([daily_scheduled])
    cron = Cron(cron_schedule="0 0 * * *")
    previous_dt = datetime.fromisoformat("2021-01-01T00:00:01")
    # 1 hour after previous_dt
    previous_launch_dt = datetime.fromisoformat("2021-01-01T00:01:01")
    # 1 hour after previous_launch_dt
    current_dt = datetime.fromisoformat("2021-01-01T00:02:01")  #
    result = cron.schedule(
        SchedulingExecutionContext(
            previous_tick_dt=previous_dt,
            tick_dt=current_dt,
            repository_def=defs.get_repository_def(),
            instance=DagsterInstance.ephemeral(),
            asset_key=daily_scheduled.key,
            previous_cursor=CronCursor(
                previous_launch_timestamp=previous_launch_dt.timestamp()
            ).serialize(),
        )
    )
    assert not result.launch
    assert result.partition_keys is None
