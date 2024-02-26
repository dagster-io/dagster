from datetime import datetime
from typing import AbstractSet, NamedTuple, Optional, Set

from dagster import (
    _check as check,
    asset,
)
from dagster._core.definitions.auto_materialize_rule import CronEvaluationData
from dagster._core.definitions.definitions_class import Definitions
from dagster._core.instance import DagsterInstance
from dagster._core.reactive_scheduling.reactive_scheduling_plan import ReactiveSchedulingGraph
from dagster._core.reactive_scheduling.scheduling_policy import (
    AssetPartition,
    SchedulingExecutionContext,
    SchedulingPolicy,
    SchedulingResult,
    TickSettings,
)
from dagster._serdes.serdes import deserialize_value, serialize_value, whitelist_for_serdes


def get_partition_keys(asset_partitions: AbstractSet[AssetPartition]) -> Optional[Set[str]]:
    if not asset_partitions:
        return set()
    if len(asset_partitions) == 1 and next(iter(asset_partitions)).partition_key is None:
        return None
    check.invariant(all(ap.partition_key is not None for ap in asset_partitions))
    check.invariant(
        {ap.asset_key for ap in asset_partitions} == {next(iter(asset_partitions)).asset_key}
    )
    return {ap.partition_key for ap in asset_partitions if ap.partition_key is not None}


@whitelist_for_serdes
class CronCursor(NamedTuple):
    previous_launch_timestamp: Optional[float]

    def serialize(self) -> str:
        return serialize_value(self)

    @staticmethod
    def deserialize(cursor: Optional[str]) -> Optional["CronCursor"]:
        return deserialize_value(cursor, as_type=CronCursor) if cursor else None


class Cron(SchedulingPolicy):
    def __init__(self, cron_schedule: str, timezone: str = "UTC") -> None:
        self.cron_schedule = cron_schedule
        self.timezone = timezone

    tick_settings = TickSettings(
        tick_cron="* * * * *",
    )

    def schedule(self, context: SchedulingExecutionContext) -> SchedulingResult:
        from dagster._core.definitions.auto_materialize_rule import (
            get_new_asset_partitions_to_request,
        )

        graph = ReactiveSchedulingGraph.from_context(context)
        asset_info = graph.get_required_asset_info(context.asset_key)

        cron_cursor = CronCursor.deserialize(context.previous_cursor)
        previous_launch_dt = (
            datetime.fromtimestamp(cron_cursor.previous_launch_timestamp)
            if cron_cursor and cron_cursor.previous_launch_timestamp
            else None
        )

        asset_partitions = get_new_asset_partitions_to_request(
            CronEvaluationData(
                cron_schedule=self.cron_schedule,
                timezone=self.timezone,
                previous_datetime=previous_launch_dt,
                current_datetime=context.tick_dt,
            ),
            asset_key=context.asset_key,
            dynamic_partitions_store=context.instance,
            partitions_def=asset_info.partitions_def,
            all_partitions=False,  # hardcode for now,
        )

        if not asset_partitions:
            return SchedulingResult(launch=False)

        return SchedulingResult(launch=True, partition_keys=get_partition_keys(asset_partitions))


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
