import datetime

from dagster._core.definitions.time_window_partitions import TimeWindow
from dagster._model import DagsterModel

from .asset_condition import AssetCondition, AssetConditionResult
from .asset_condition_evaluation_context import AssetConditionEvaluationContext


class Duration(DagsterModel):
    days: float = 0
    hours: float = 0
    minutes: float = 0

    def __repr__(self) -> str:
        if self.days == self.hours == self.minutes == 0:
            return "0 minutes"

        return ", ".join(
            f"{v} {unit}"
            for v, unit in (
                (self.days, "days"),
                (self.hours, "hours"),
                (self.minutes, "minutes"),
            )
            if v != 0
        )

    def to_timedelta(self) -> datetime.timedelta:
        return datetime.timedelta(
            days=self.days,
            hours=self.hours,
            minutes=self.minutes,
        )


class RecentTimePartitionsCondition(AssetCondition):
    lookback_duration: Duration

    @property
    def description(self) -> str:
        return f"Asset partition is within a time window starting {self.lookback_duration} before the current time, or is not time-partitioned."

    def evaluate(self, context: AssetConditionEvaluationContext) -> AssetConditionResult:
        return AssetConditionResult.create(
            context,
            true_subset=context.asset_graph_view.create_time_window_slice(
                asset_key=context.asset_key,
                time_window=TimeWindow(
                    start=context.evaluation_time - self.lookback_duration.to_timedelta(),
                    end=context.evaluation_time,
                ),
            ).convert_to_valid_asset_subset(),
        )
