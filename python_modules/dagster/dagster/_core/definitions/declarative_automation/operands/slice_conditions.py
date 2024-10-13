import datetime
from abc import abstractmethod
from typing import Optional

from dagster._core.asset_graph_view.entity_subset import EntitySubset
from dagster._core.definitions.asset_key import AssetKey, T_EntityKey
from dagster._core.definitions.declarative_automation.automation_condition import (
    AutomationResult,
    BuiltinAutomationCondition,
)
from dagster._core.definitions.declarative_automation.automation_context import AutomationContext
from dagster._core.definitions.declarative_automation.utils import SerializableTimeDelta
from dagster._record import record
from dagster._serdes.serdes import whitelist_for_serdes
from dagster._utils.schedules import reverse_cron_string_iterator


@record
@whitelist_for_serdes
class InitialEvaluationCondition(BuiltinAutomationCondition):
    """Condition to determine if this is the initial evaluation of a given AutomationCondition."""

    @property
    def description(self) -> str:
        return "Initial evaluation"

    @property
    def name(self) -> str:
        return "initial_evaluation"

    def evaluate(self, context: AutomationContext) -> AutomationResult:
        condition_tree_id = context.root_context.condition.get_unique_id()
        if context.previous_true_subset is None or condition_tree_id != context.cursor:
            subset = context.candidate_subset
        else:
            subset = context.get_empty_subset()
        return AutomationResult(context, subset, cursor=condition_tree_id)


@record
class SubsetAutomationCondition(BuiltinAutomationCondition[T_EntityKey]):
    """Base class for simple conditions which compute a simple subset of the asset graph."""

    @property
    def requires_cursor(self) -> bool:
        return False

    @abstractmethod
    def compute_subset(
        self, context: AutomationContext[T_EntityKey]
    ) -> EntitySubset[T_EntityKey]: ...

    def evaluate(self, context: AutomationContext[T_EntityKey]) -> AutomationResult[T_EntityKey]:
        # don't compute anything if there are no candidates
        if context.candidate_subset.is_empty:
            true_subset = context.get_empty_subset()
        else:
            true_subset = self.compute_subset(context)

        return AutomationResult(context, true_subset)


@whitelist_for_serdes
@record
class MissingAutomationCondition(SubsetAutomationCondition[AssetKey]):
    @property
    def description(self) -> str:
        return "Missing"

    @property
    def name(self) -> str:
        return "missing"

    def compute_subset(self, context: AutomationContext) -> EntitySubset[AssetKey]:
        return context.asset_graph_view.compute_missing_subset(
            context.key, from_subset=context.candidate_subset
        )


@whitelist_for_serdes
@record
class InProgressAutomationCondition(SubsetAutomationCondition[AssetKey]):
    @property
    def description(self) -> str:
        return "Part of an in-progress run"

    @property
    def name(self) -> str:
        return "in_progress"

    def compute_subset(self, context: AutomationContext) -> EntitySubset[AssetKey]:
        return context.asset_graph_view.compute_in_progress_asset_subset(asset_key=context.key)


@whitelist_for_serdes
@record
class FailedAutomationCondition(SubsetAutomationCondition[AssetKey]):
    @property
    def description(self) -> str:
        return "Latest run failed"

    @property
    def name(self) -> str:
        return "failed"

    def compute_subset(self, context: AutomationContext) -> EntitySubset[AssetKey]:
        return context.asset_graph_view.compute_failed_asset_subset(asset_key=context.key)


@whitelist_for_serdes
@record
class WillBeRequestedCondition(SubsetAutomationCondition[AssetKey]):
    @property
    def description(self) -> str:
        return "Will be requested this tick"

    @property
    def name(self) -> str:
        return "will_be_requested"

    def _executable_with_root_context_key(self, context: AutomationContext) -> bool:
        # TODO: once we can launch backfills via the asset daemon, this can be removed
        from dagster._core.definitions.asset_graph import executable_in_same_run

        root_key = context.root_context.key
        return executable_in_same_run(
            asset_graph=context.asset_graph_view.asset_graph,
            child_key=root_key,
            parent_key=context.key,
        )

    def compute_subset(self, context: AutomationContext) -> EntitySubset[AssetKey]:
        current_result = context.current_results_by_key.get(context.key)
        if (
            current_result
            and current_result.true_subset
            and self._executable_with_root_context_key(context)
        ):
            return current_result.true_subset
        else:
            return context.get_empty_subset()


@whitelist_for_serdes
@record
class NewlyRequestedCondition(SubsetAutomationCondition[AssetKey]):
    @property
    def description(self) -> str:
        return "Was requested on the previous tick"

    @property
    def name(self) -> str:
        return "newly_requested"

    def compute_subset(self, context: AutomationContext) -> EntitySubset[AssetKey]:
        return context.previous_requested_subset or context.get_empty_subset()


@whitelist_for_serdes
@record
class NewlyUpdatedCondition(SubsetAutomationCondition[AssetKey]):
    @property
    def description(self) -> str:
        return "Updated since previous tick"

    @property
    def name(self) -> str:
        return "newly_updated"

    def compute_subset(self, context: AutomationContext) -> EntitySubset[AssetKey]:
        # if it's the first time evaluating, just return the empty subset
        if context.previous_evaluation_time is None:
            return context.get_empty_subset()
        else:
            return context.asset_graph_view.compute_updated_since_cursor_subset(
                asset_key=context.key, cursor=context.previous_max_storage_id
            )


@whitelist_for_serdes
@record
class CronTickPassedCondition(SubsetAutomationCondition):
    cron_schedule: str
    cron_timezone: str

    @property
    def description(self) -> str:
        return f"New tick of {self.cron_schedule} ({self.cron_timezone})"

    @property
    def name(self) -> str:
        return "cron_tick_passed"

    def _get_previous_cron_tick(self, effective_dt: datetime.datetime) -> datetime.datetime:
        previous_ticks = reverse_cron_string_iterator(
            end_timestamp=effective_dt.timestamp(),
            cron_string=self.cron_schedule,
            execution_timezone=self.cron_timezone,
        )
        return next(previous_ticks)

    def compute_subset(self, context: AutomationContext) -> EntitySubset:
        previous_cron_tick = self._get_previous_cron_tick(context.evaluation_time)
        if (
            # no previous evaluation
            context.previous_evaluation_time is None
            # cron tick was not newly passed
            or previous_cron_tick < context.previous_evaluation_time
        ):
            return context.get_empty_subset()
        else:
            return context.candidate_subset


@whitelist_for_serdes
@record
class InLatestTimeWindowCondition(SubsetAutomationCondition[AssetKey]):
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

    @property
    def name(self) -> str:
        return "in_latest_time_window"

    def compute_subset(self, context: AutomationContext) -> EntitySubset[AssetKey]:
        return context.asset_graph_view.compute_latest_time_window_subset(
            context.key, lookback_delta=self.lookback_timedelta
        )
