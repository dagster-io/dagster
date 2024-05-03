import datetime
from abc import abstractmethod
from typing import Optional, Tuple

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
class WillBeRequestedCondition(SliceSchedulingCondition):
    @property
    def description(self) -> str:
        return "Will be requested this tick"

    def _executable_with_root_context_key(self, context: SchedulingContext) -> bool:
        # TODO: once we can launch backfills via the asset daemon, this can be removed
        root_key = context.root_context.asset_key
        return context.legacy_context.materializable_in_same_run(
            child_key=root_key, parent_key=context.asset_key
        )

    def compute_slice(self, context: SchedulingContext) -> AssetSlice:
        current_info = context.current_tick_evaluation_info_by_key.get(context.asset_key)
        if (
            current_info
            and current_info.requested_slice
            and self._executable_with_root_context_key(context)
        ):
            return current_info.requested_slice
        else:
            return context.asset_graph_view.create_empty_slice(context.asset_key)


@whitelist_for_serdes
class InLatestTimeWindowCondition(SliceSchedulingCondition):
    # This is a serializable representation of the lookback timedelta object
    lookback_days_second_microseconds: Optional[Tuple[int, int, int]] = None

    @staticmethod
    def from_lookback_delta(
        lookback_delta: Optional[datetime.timedelta],
    ) -> "InLatestTimeWindowCondition":
        lookback_days_second_microseconds = (
            (
                lookback_delta.days,
                lookback_delta.seconds,
                lookback_delta.microseconds,
            )
            if lookback_delta
            else None
        )
        return InLatestTimeWindowCondition(
            lookback_days_second_microseconds=lookback_days_second_microseconds
        )

    @property
    def timedelta(self) -> Optional[datetime.timedelta]:
        if self.lookback_days_second_microseconds:
            return datetime.timedelta(
                days=self.lookback_days_second_microseconds[0],
                seconds=self.lookback_days_second_microseconds[1],
                microseconds=self.lookback_days_second_microseconds[2],
            )
        else:
            return None

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
