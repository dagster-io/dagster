import datetime
from abc import abstractmethod
from typing import Optional

from dagster._core.asset_graph_view.asset_graph_view import AssetSlice
from dagster._serdes.serdes import whitelist_for_serdes

from ..legacy.asset_condition import AssetCondition
from ..scheduling_condition import SchedulingResult
from ..scheduling_context import SchedulingContext


class SliceSchedulingCondition(AssetCondition):
    """Base class for simple conditions which compute a simple slice of the asset graph."""

    @abstractmethod
    def compute_slice(self, context: SchedulingContext) -> AssetSlice: ...

    def evaluate(self, context: SchedulingContext) -> SchedulingResult:
        # don't compute anything if there are no candidates
        if context.candidate_slice.is_empty:
            true_slice = context.asset_graph_view.create_empty_slice(context.asset_key)
        else:
            true_slice = self.compute_slice(context)

        return SchedulingResult.create(context, true_slice)


@whitelist_for_serdes
class MissingSchedulingCondition(SliceSchedulingCondition):
    @property
    def description(self) -> str:
        return "Missing"

    def compute_slice(self, context: SchedulingContext) -> AssetSlice:
        return context.asset_graph_view.compute_missing_subslice(
            context.asset_key, from_slice=context.candidate_slice
        )


@whitelist_for_serdes
class InProgressSchedulingCondition(SliceSchedulingCondition):
    @property
    def description(self) -> str:
        return "Part of an in-progress run"

    def compute_slice(self, context: SchedulingContext) -> AssetSlice:
        return context.asset_graph_view.compute_in_progress_asset_slice(context.asset_key)


@whitelist_for_serdes
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

    def compute_slice(self, context: SchedulingContext) -> AssetSlice:
        return context.asset_graph_view.compute_latest_time_window_slice(
            context.asset_key, lookback_delta=self.timedelta
        )
