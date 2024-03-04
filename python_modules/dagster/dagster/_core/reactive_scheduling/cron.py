from typing import NamedTuple, Optional

from dagster._core.reactive_scheduling.asset_graph_view import AssetSlice
from dagster._core.reactive_scheduling.scheduling_policy import (
    ScheduleLaunchResult,
    SchedulingExecutionContext,
    SchedulingPolicy,
)
from dagster._serdes.serdes import deserialize_value, serialize_value, whitelist_for_serdes


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

    # tick_settings = TickSettings(
    #     tick_cron="* * * * *",
    # )

    def schedule_launch(
        self, context: SchedulingExecutionContext, asset_slice: AssetSlice
    ) -> ScheduleLaunchResult:
        cron_cursor = CronCursor.deserialize(context.previous_cursor)
        # previous_launch_dt = (
        #     pendulum.from_timestamp(cron_cursor.previous_launch_timestamp)
        #     if cron_cursor and cron_cursor.previous_launch_timestamp
        #     else None
        # )

        # TODO implement
        asset_slice_since_cron = context.asset_graph_view.slice_factory.empty(asset_slice.asset_key)
        # asset_slice_since_cron = graph.get_partition_range_since_cron(
        #     asset_key=context.ticked_asset_key,
        #     cron_data=CronEvaluationData(
        #         cron_schedule=self.cron_schedule,
        #         timezone=self.timezone,
        #         previous_datetime=previous_launch_dt,
        #         current_datetime=context.tick_dt,
        #     ),
        # )

        if asset_slice_since_cron.is_empty:
            return ScheduleLaunchResult(
                launch=False, cursor=cron_cursor.serialize() if cron_cursor else None
            )

        return ScheduleLaunchResult(
            launch=True,
            explicit_launching_slice=asset_slice_since_cron,
            cursor=CronCursor(
                previous_launch_timestamp=context.effective_dt.timestamp()
            ).serialize(),
        )
