import datetime
from abc import abstractmethod
from typing import Optional

from dagster._core.asset_graph_view.asset_graph_view import AssetSlice

from .asset_condition import AssetCondition, AssetConditionResult
from .scheduling_condition_evaluation_context import SchedulingConditionEvaluationContext


class SliceSchedulingCondition(AssetCondition):
    """Base class for simple conditions which compute a simple slice of the asset graph."""

    @abstractmethod
    def compute_slice(self, context: SchedulingConditionEvaluationContext) -> AssetSlice: ...

    def evaluate(self, context: SchedulingConditionEvaluationContext) -> AssetConditionResult:
        # don't compute anything if there are no candidates
        if context.candidate_slice.is_empty:
            true_slice = context.asset_graph_view.create_empty_slice(context.asset_key)
        else:
            true_slice = self.compute_slice(context)

        return AssetConditionResult.create(context, true_slice.convert_to_valid_asset_subset())


class MissingSchedulingCondition(SliceSchedulingCondition):
    @property
    def description(self) -> str:
        return "Missing"

    def compute_slice(self, context: SchedulingConditionEvaluationContext) -> AssetSlice:
        return context.asset_graph_view.compute_missing_subslice(
            context.asset_key, from_slice=context.candidate_slice
        )


class InProgressSchedulingCondition(SliceSchedulingCondition):
    @property
    def description(self) -> str:
        return "Part of an in-progress run"

    def compute_slice(self, context: SchedulingConditionEvaluationContext) -> AssetSlice:
        return context.asset_graph_view.compute_in_progress_asset_slice(context.asset_key)


class InLatestTimeWindowCondition(SliceSchedulingCondition):
    lookback_seconds: Optional[float] = None

    @property
    def timedelta(self) -> Optional[datetime.timedelta]:
        return datetime.timedelta(seconds=self.lookback_seconds) if self.lookback_seconds else None

    @property
    def description(self) -> str:
        return (
            f"Within {self.timedelta} of the end of the latest time window"
            if self.timedelta
            else "Within latest time window"
        )

    def compute_slice(self, context: SchedulingConditionEvaluationContext) -> AssetSlice:
        return context.asset_graph_view.compute_latest_time_window_slice(
            context.asset_key, lookback_delta=self.timedelta
        )
