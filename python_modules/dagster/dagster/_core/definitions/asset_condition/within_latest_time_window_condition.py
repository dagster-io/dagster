import datetime
from typing import Optional

from dagster._core.definitions.asset_condition.asset_condition import (
    AssetCondition,
    AssetConditionResult,
)

from .asset_condition_evaluation_context import AssetConditionEvaluationContext


class WithinLatestTimeWindowCondition(AssetCondition):
    """A condition which evaluates to True for asset partitions that are not time-partitioned, or
    have time-partition keys within a specified delta of the evaluation time. If no delta is set,
    then only the latest time partition will evaluate to True.
    """

    delta_days: Optional[int] = None
    delta_hours: Optional[int] = None
    delta_minutes: Optional[int] = None

    @property
    def description(self) -> str:
        if self.latest_only:
            return "Asset partition is within the latest time window, or is not time-partitioned."
        else:
            time_window_str = ", ".join(
                f"{v} {unit}"
                for v, unit in (
                    (self.delta_days, "days"),
                    (self.delta_hours, "hours"),
                    (self.delta_minutes, "minutes"),
                )
                if v is not None
            )
            return f"Asset partition is within a time window starting {time_window_str} before the current time, or is not time-partitioned."

    @property
    def latest_only(self) -> bool:
        return all(d is None for d in (self.delta_days, self.delta_hours, self.delta_minutes))

    @property
    def timedelta(self) -> Optional[datetime.timedelta]:
        if self.latest_only:
            return None
        return datetime.timedelta(
            days=self.delta_days or 0,
            hours=self.delta_hours or 0,
            minutes=self.delta_minutes or 0,
        )

    def evaluate(self, context: AssetConditionEvaluationContext) -> AssetConditionResult:
        return AssetConditionResult.create(
            context,
            true_subset=context.asset_graph_view.create_latest_time_window_slice(
                context.asset_key, timedelta=self.timedelta
            ).convert_to_valid_asset_subset(),
        )
