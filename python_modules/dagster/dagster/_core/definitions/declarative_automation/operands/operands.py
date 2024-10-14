import datetime
from typing import Optional

from dagster._core.asset_graph_view.entity_subset import EntitySubset
from dagster._core.definitions.asset_key import AssetCheckKey, AssetKey
from dagster._core.definitions.declarative_automation.automation_condition import (
    AutomationResult,
    BuiltinAutomationCondition,
)
from dagster._core.definitions.declarative_automation.automation_context import AutomationContext
from dagster._core.definitions.declarative_automation.operands.subset_automation_condition import (
    SubsetAutomationCondition,
)
from dagster._core.definitions.declarative_automation.utils import SerializableTimeDelta
from dagster._record import record
from dagster._serdes.serdes import whitelist_for_serdes
from dagster._utils.schedules import reverse_cron_string_iterator


@whitelist_for_serdes
@record
class CodeVersionChangedCondition(BuiltinAutomationCondition[AssetKey]):
    @property
    def name(self) -> str:
        return "code_version_changed"

    def evaluate(self, context: AutomationContext) -> AutomationResult[AssetKey]:
        previous_code_version = context.cursor
        current_code_version = context.asset_graph.get(context.key).code_version
        if previous_code_version is None or previous_code_version == current_code_version:
            true_subset = context.get_empty_subset()
        else:
            true_subset = context.candidate_subset

        return AutomationResult(context, true_subset, cursor=current_code_version)


@record
@whitelist_for_serdes
class InitialEvaluationCondition(BuiltinAutomationCondition):
    """Condition to determine if this is the initial evaluation of a given AutomationCondition."""

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


@whitelist_for_serdes
@record
class MissingAutomationCondition(SubsetAutomationCondition):
    @property
    def name(self) -> str:
        return "missing"

    async def compute_subset(self, context: AutomationContext) -> EntitySubset:
        return await context.asset_graph_view.compute_missing_subset(
            key=context.key, from_subset=context.candidate_subset
        )


@whitelist_for_serdes(storage_name="InProgressAutomationCondition")
@record
class RunInProgressAutomationCondition(SubsetAutomationCondition):
    @property
    def name(self) -> str:
        return "execution_in_progress"

    def compute_subset(self, context: AutomationContext) -> EntitySubset:
        return context.asset_graph_view.compute_run_in_progress_subset(key=context.key)


@whitelist_for_serdes
@record
class BackfillInProgressAutomationCondition(SubsetAutomationCondition):
    @property
    def name(self) -> str:
        return "backfill_in_progress"

    def compute_subset(self, context: AutomationContext) -> EntitySubset:
        return context.asset_graph_view.compute_backfill_in_progress_subset(key=context.key)


@whitelist_for_serdes(storage_name="FailedAutomationCondition")
@record
class ExecutionFailedAutomationCondition(SubsetAutomationCondition):
    @property
    def name(self) -> str:
        return "execution_failed"

    async def compute_subset(self, context: AutomationContext) -> EntitySubset:
        return await context.asset_graph_view.compute_execution_failed_subset(key=context.key)


@whitelist_for_serdes
@record
class WillBeRequestedCondition(SubsetAutomationCondition):
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

    def compute_subset(self, context: AutomationContext) -> EntitySubset:
        current_result = context.request_subsets_by_key.get(context.key)
        if current_result and self._executable_with_root_context_key(context):
            return current_result
        else:
            return context.get_empty_subset()


@whitelist_for_serdes
@record
class NewlyRequestedCondition(SubsetAutomationCondition):
    @property
    def name(self) -> str:
        return "newly_requested"

    def compute_subset(self, context: AutomationContext) -> EntitySubset:
        return context.previous_requested_subset or context.get_empty_subset()


@whitelist_for_serdes
@record
class NewlyUpdatedCondition(SubsetAutomationCondition):
    @property
    def name(self) -> str:
        return "newly_updated"

    def compute_subset(self, context: AutomationContext) -> EntitySubset:
        # if it's the first time evaluating, just return the empty subset
        if context.previous_temporal_context is None:
            return context.get_empty_subset()
        return context.asset_graph_view.compute_updated_since_temporal_context_subset(
            key=context.key, temporal_context=context.previous_temporal_context
        )


@whitelist_for_serdes
@record
class CronTickPassedCondition(SubsetAutomationCondition):
    cron_schedule: str
    cron_timezone: str

    @property
    def name(self) -> str:
        return f"cron_tick_passed(cron_schedule={self.cron_schedule}, cron_timezone={self.cron_timezone})"

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
class InLatestTimeWindowCondition(SubsetAutomationCondition):
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
        name = "in_latest_time_window"
        if self.serializable_lookback_timedelta:
            name += f"(lookback_timedelta={self.lookback_timedelta})"
        return name

    def compute_subset(self, context: AutomationContext) -> EntitySubset:
        return context.asset_graph_view.compute_latest_time_window_subset(
            context.key, lookback_delta=self.lookback_timedelta
        )


@whitelist_for_serdes
@record
class CheckResultCondition(SubsetAutomationCondition[AssetCheckKey]):
    passed: bool

    @property
    def name(self) -> str:
        return "check_passed" if self.passed else "check_failed"

    def compute_subset(
        self, context: AutomationContext[AssetCheckKey]
    ) -> EntitySubset[AssetCheckKey]:
        from dagster._core.storage.asset_check_execution_record import (
            AssetCheckExecutionResolvedStatus,
        )

        target_status = (
            AssetCheckExecutionResolvedStatus.SUCCEEDED
            if self.passed
            else AssetCheckExecutionResolvedStatus.FAILED
        )
        return context.asset_graph_view.compute_subset_with_status(
            key=context.key, status=target_status
        )
