import datetime
from abc import abstractmethod
from typing import Optional

from dagster._core.asset_graph_view.asset_graph_view import AssetSlice
from dagster._core.definitions.declarative_automation.utils import SerializableTimeDelta
from dagster._serdes.serdes import whitelist_for_serdes
from dagster._utils.schedules import reverse_cron_string_iterator

from ..automation_condition import AutomationCondition, AutomationResult
from ..automation_context import AutomationContext


class SliceAutomationCondition(AutomationCondition):
    """Base class for simple conditions which compute a simple slice of the asset graph."""

    @abstractmethod
    def compute_slice(self, context: AutomationContext) -> AssetSlice: ...

    def evaluate(self, context: AutomationContext) -> AutomationResult:
        # don't compute anything if there are no candidates
        if context.candidate_slice.is_empty:
            true_slice = context.asset_graph_view.create_empty_slice(asset_key=context.asset_key)
        else:
            true_slice = self.compute_slice(context)

        return AutomationResult.create(context, true_slice)


@whitelist_for_serdes
class MissingAutomationCondition(SliceAutomationCondition):
    @property
    def description(self) -> str:
        return "Missing"

    def compute_slice(self, context: AutomationContext) -> AssetSlice:
        return context.asset_graph_view.compute_missing_subslice(
            context.asset_key, from_slice=context.candidate_slice
        )


@whitelist_for_serdes
class InProgressAutomationCondition(SliceAutomationCondition):
    @property
    def description(self) -> str:
        return "Part of an in-progress run"

    def compute_slice(self, context: AutomationContext) -> AssetSlice:
        return context.asset_graph_view.compute_in_progress_asset_slice(asset_key=context.asset_key)


@whitelist_for_serdes
class FailedAutomationCondition(SliceAutomationCondition):
    @property
    def description(self) -> str:
        return "Latest run failed"

    def compute_slice(self, context: AutomationContext) -> AssetSlice:
        return context.asset_graph_view.compute_failed_asset_slice(asset_key=context.asset_key)


@whitelist_for_serdes
class WillBeRequestedCondition(SliceAutomationCondition):
    @property
    def description(self) -> str:
        return "Will be requested this tick"

    def _executable_with_root_context_key(self, context: AutomationContext) -> bool:
        # TODO: once we can launch backfills via the asset daemon, this can be removed
        from dagster._core.definitions.asset_graph import materializable_in_same_run

        root_key = context.root_context.asset_key
        return materializable_in_same_run(
            asset_graph=context.asset_graph_view.asset_graph,
            child_key=root_key,
            parent_key=context.asset_key,
        )

    def compute_slice(self, context: AutomationContext) -> AssetSlice:
        current_result = context.current_tick_results_by_key.get(context.asset_key)
        if (
            current_result
            and current_result.true_slice
            and self._executable_with_root_context_key(context)
        ):
            return current_result.true_slice
        else:
            return context.asset_graph_view.create_empty_slice(asset_key=context.asset_key)


@whitelist_for_serdes
class NewlyRequestedCondition(SliceAutomationCondition):
    @property
    def description(self) -> str:
        return "Was requested on the previous tick"

    def compute_slice(self, context: AutomationContext) -> AssetSlice:
        return context.previous_requested_slice or context.asset_graph_view.create_empty_slice(
            asset_key=context.asset_key
        )


@whitelist_for_serdes
class NewlyUpdatedCondition(SliceAutomationCondition):
    @property
    def description(self) -> str:
        return "Updated since previous tick"

    def compute_slice(self, context: AutomationContext) -> AssetSlice:
        # if it's the first time evaluating, just return the empty slice
        if context.cursor is None:
            return context.asset_graph_view.create_empty_slice(asset_key=context.asset_key)
        else:
            return context.asset_graph_view.compute_updated_since_cursor_slice(
                asset_key=context.asset_key, cursor=context.previous_evaluation_max_storage_id
            )


@whitelist_for_serdes
class CronTickPassedCondition(SliceAutomationCondition):
    cron_schedule: str
    cron_timezone: str

    @property
    def description(self) -> str:
        return f"New tick of {self.cron_schedule} ({self.cron_timezone})"

    def _get_previous_cron_tick(self, effective_dt: datetime.datetime) -> datetime.datetime:
        previous_ticks = reverse_cron_string_iterator(
            end_timestamp=effective_dt.timestamp(),
            cron_string=self.cron_schedule,
            execution_timezone=self.cron_timezone,
        )
        return next(previous_ticks)

    def compute_slice(self, context: AutomationContext) -> AssetSlice:
        previous_cron_tick = self._get_previous_cron_tick(context.effective_dt)
        if (
            # no previous evaluation
            context.previous_evaluation_effective_dt is None
            # cron tick was not newly passed
            or previous_cron_tick < context.previous_evaluation_effective_dt
        ):
            return context.asset_graph_view.create_empty_slice(asset_key=context.asset_key)
        else:
            return context.candidate_slice


@whitelist_for_serdes
class InLatestTimeWindowCondition(SliceAutomationCondition):
    serializable_lookback_timedelta: Optional[SerializableTimeDelta] = None

    @staticmethod
    def from_lookback_delta(
        lookback_delta: Optional[datetime.timedelta],
    ) -> "InLatestTimeWindowCondition":
        return InLatestTimeWindowCondition(
            serializable_lookback_timedelta=SerializableTimeDelta.from_timedelta(lookback_delta)
            if lookback_delta
            else None
        )

    @property
    def lookback_timedelta(self) -> Optional[datetime.timedelta]:
        return (
            self.serializable_lookback_timedelta.to_timedelta()
            if self.serializable_lookback_timedelta
            else None
        )

    @property
    def description(self) -> str:
        return (
            f"Within {self.lookback_timedelta} of the end of the latest time window"
            if self.lookback_timedelta
            else "Within latest time window"
        )

    def compute_slice(self, context: AutomationContext) -> AssetSlice:
        return context.asset_graph_view.compute_latest_time_window_slice(
            context.asset_key, lookback_delta=self.lookback_timedelta
        )
