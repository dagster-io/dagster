import datetime
import logging
import os

from dagster_shared.serdes import whitelist_for_serdes
from dagster_shared.serdes.utils import SerializableTimeDelta

from dagster._core.asset_graph_view.entity_subset import EntitySubset
from dagster._core.asset_graph_view.timing_metadata import TimingMetadata
from dagster._core.definitions.asset_key import AssetCheckKey, AssetKey
from dagster._core.definitions.declarative_automation.automation_condition import (
    AutomationResult,
    BuiltinAutomationCondition,
)
from dagster._core.definitions.declarative_automation.automation_context import AutomationContext
from dagster._core.definitions.declarative_automation.operands.subset_automation_condition import (
    SubsetAutomationCondition,
    TimedSubsetAutomationCondition,
)
from dagster._core.definitions.freshness import FreshnessState
from dagster._core.definitions.partitions.snap.snap import PartitionsSnap
from dagster._core.definitions.partitions.subset.key_ranges import KeyRangesPartitionsSubset
from dagster._record import record
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


@whitelist_for_serdes
@record
class InitialEvaluationCondition(BuiltinAutomationCondition):
    """Condition to determine if this is the initial evaluation of a given AutomationCondition with a particular PartitionsDefinition."""

    @property
    def name(self) -> str:
        return "initial_evaluation"

    def _is_initial_evaluation(self, context: AutomationContext) -> bool:
        root_key = context.root_context.key
        previous_requested_subset = context.get_previous_requested_subset(root_key)
        if previous_requested_subset is None:
            return True

        previous_subset_value = previous_requested_subset.get_internal_value()
        previous_subset_value_type = type(previous_subset_value)

        current_subset = context.asset_graph_view.get_empty_subset(key=context.root_context.key)
        current_subset_value_type = type(current_subset.get_internal_value())
        # if we have a key ranges subset, we can compare the partitions snapshot
        if isinstance(previous_subset_value, KeyRangesPartitionsSubset):
            current_partitions_snap = (
                PartitionsSnap.from_def(context.partitions_def) if context.partitions_def else None
            )
            previous_partitions_snap = previous_subset_value.partitions_snap
            return previous_partitions_snap != current_partitions_snap

        return previous_subset_value_type != current_subset_value_type

    def evaluate(self, context: AutomationContext) -> AutomationResult:
        # we retain the condition_tree_id as a cursor despite it being unused as
        # earlier iterations of this condition used it and we want to retain the
        # option value of reverting this in the future
        condition_tree_id = context.root_context.condition.get_unique_id()
        if self._is_initial_evaluation(context):
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

    async def compute_subset(self, context: AutomationContext) -> EntitySubset:  # pyright: ignore[reportIncompatibleMethodOverride]
        return await context.asset_graph_view.compute_missing_subset(
            key=context.key, from_subset=context.candidate_subset
        )


@whitelist_for_serdes(storage_name="InProgressAutomationCondition")
@record
class RunInProgressAutomationCondition(SubsetAutomationCondition):
    @property
    def name(self) -> str:
        return "run_in_progress"

    async def compute_subset(self, context: AutomationContext) -> EntitySubset:  # pyright: ignore[reportIncompatibleMethodOverride]
        return await context.asset_graph_view.compute_run_in_progress_subset(
            key=context.key, from_subset=context.candidate_subset
        )


@whitelist_for_serdes
@record
class BackfillInProgressAutomationCondition(SubsetAutomationCondition):
    @property
    def name(self) -> str:
        return "backfill_in_progress"

    async def compute_subset(self, context: AutomationContext) -> EntitySubset:  # pyright: ignore[reportIncompatibleMethodOverride]
        return await context.asset_graph_view.compute_backfill_in_progress_subset(
            key=context.key, from_subset=context.candidate_subset
        )


@whitelist_for_serdes(storage_name="FailedAutomationCondition")
@record
class ExecutionFailedAutomationCondition(SubsetAutomationCondition):
    @property
    def name(self) -> str:
        return "execution_failed"

    async def compute_subset(self, context: AutomationContext) -> EntitySubset:  # pyright: ignore[reportIncompatibleMethodOverride]
        return await context.asset_graph_view.compute_execution_failed_subset(
            key=context.key, from_subset=context.candidate_subset
        )


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
        from dagster._core.definitions.assets.graph.asset_graph import executable_in_same_run

        root_key = context.root_context.key
        if not executable_in_same_run(
            asset_graph=context.asset_graph_view.asset_graph,
            child_key=root_key,
            parent_key=context.key,
        ):
            return False
        elif not isinstance(context.key, AssetKey):
            return True
        else:
            # if the parent is an asset key, it must be materializable in order
            # for updates to be guaranteed to count as updates to the downstream
            # for the purposes of the `newly_updated` condition. therefore, we
            # need this check to prevent cases where we combine an observable
            # source execution and a materialization in the same run with the
            # expectation that the observation will result in a new data version
            return context.asset_graph.get(context.key).is_materializable

    def compute_subset(self, context: AutomationContext) -> EntitySubset:
        current_result = context.request_subsets_by_key.get(context.key)
        if current_result and self._executable_with_root_context_key(context):
            return current_result
        else:
            return context.get_empty_subset()


@whitelist_for_serdes
@record
class NewlyRequestedCondition(TimedSubsetAutomationCondition):
    @property
    def name(self) -> str:
        return "newly_requested"

    def compute_subset_with_timing_metadata(
        self, context: AutomationContext
    ) -> tuple[EntitySubset, TimingMetadata | None]:
        subset = context.get_previous_requested_subset(context.key) or context.get_empty_subset()
        if subset.is_empty or context.previous_evaluation_time is None:
            return subset, None
        return subset, TimingMetadata(
            timestamps={context.previous_evaluation_time.timestamp(): subset}
        )


@whitelist_for_serdes
@record
class NewlyUpdatedCondition(TimedSubsetAutomationCondition):
    @property
    def name(self) -> str:
        return "newly_updated"

    async def compute_subset_with_timing_metadata(  # pyright: ignore[reportIncompatibleMethodOverride]
        self, context: AutomationContext
    ) -> tuple[EntitySubset, TimingMetadata | None]:
        # if it's the first time evaluating, just return the empty subset
        if context.previous_temporal_context is None:
            return context.get_empty_subset(), None

        if not isinstance(context.key, AssetKey):
            # For non-asset keys (e.g. checks), no timestamp enrichment yet
            subset = await context.asset_graph_view.compute_updated_since_temporal_context_subset(
                key=context.key, temporal_context=context.previous_temporal_context
            )
            return subset, None

        subset = await context.asset_graph_view.compute_updated_since_temporal_context_subset(
            key=context.key, temporal_context=context.previous_temporal_context
        )
        if subset.is_empty:
            return subset, None

        max_partitions = int(os.environ.get("DAGSTER_MAX_PARTITIONS_FOR_DA_TIMESTAMP_FETCH", "100"))
        if subset.size > max_partitions:
            # Too many partitions to fetch individual timestamps — use the current
            # tick timestamp for the entire subset so that downstream SinceCondition
            # logic still has timing metadata to work with.
            logging.getLogger("dagster").warning(
                "Asset %s has %d updated partitions, exceeding the maximum of %d for"
                " per-partition timestamp fetching. Using tick timestamp as fallback.",
                context.key.to_user_string(),
                subset.size,
                max_partitions,
            )
            return subset, TimingMetadata(
                timestamps={context.asset_graph_view.effective_dt.timestamp(): subset}
            )

        timing_subsets = (
            context.asset_graph_view.compute_subsets_by_latest_materialization_timestamp(subset)
        )
        if not timing_subsets:
            return subset, None
        return subset, TimingMetadata(timestamps=timing_subsets)


@whitelist_for_serdes
@record
class FreshnessResultCondition(SubsetAutomationCondition[AssetKey]):
    state: FreshnessState

    @property
    def name(self) -> str:
        return f"freshness_result(state={self.state})"

    async def compute_subset(self, context: AutomationContext[AssetKey]) -> EntitySubset[AssetKey]:  # pyright: ignore[reportIncompatibleMethodOverride]
        return await context.asset_graph_view.compute_subset_with_freshness_state(
            key=context.key, state=self.state
        )


@whitelist_for_serdes
@record
class DataVersionChangedCondition(SubsetAutomationCondition):
    @property
    def name(self) -> str:
        return "data_version_changed"

    async def compute_subset(self, context: AutomationContext) -> EntitySubset:  # pyright: ignore[reportIncompatibleMethodOverride]
        # if it's the first time evaluating, just return the empty subset
        if context.previous_temporal_context is None:
            return context.get_empty_subset()
        return await context.asset_graph_view.compute_data_version_changed_since_temporal_context_subset(
            key=context.key, temporal_context=context.previous_temporal_context
        )


@whitelist_for_serdes
@record
class CronTickPassedCondition(TimedSubsetAutomationCondition):
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

    def compute_subset_with_timing_metadata(
        self, context: AutomationContext
    ) -> tuple[EntitySubset, TimingMetadata | None]:
        previous_cron_tick = self._get_previous_cron_tick(context.evaluation_time)
        if (
            # no previous evaluation
            context.previous_evaluation_time is None
            # cron tick was not newly passed
            or previous_cron_tick < context.previous_evaluation_time
        ):
            return context.get_empty_subset(), None
        else:
            candidate_subset = context.candidate_subset
            cron_tick_ts = previous_cron_tick.timestamp()
            return candidate_subset, TimingMetadata(timestamps={cron_tick_ts: candidate_subset})


@whitelist_for_serdes
@record
class InLatestTimeWindowCondition(SubsetAutomationCondition):
    serializable_lookback_timedelta: SerializableTimeDelta | None = None

    @staticmethod
    def from_lookback_delta(
        lookback_delta: datetime.timedelta | None,
    ) -> "InLatestTimeWindowCondition":
        return InLatestTimeWindowCondition(
            serializable_lookback_timedelta=SerializableTimeDelta.from_timedelta(lookback_delta)
            if lookback_delta
            else None
        )

    @property
    def lookback_timedelta(self) -> datetime.timedelta | None:
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

    async def compute_subset(  # pyright: ignore[reportIncompatibleMethodOverride]
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
        return await context.asset_graph_view.compute_subset_with_status(
            key=context.key, status=target_status, from_subset=context.candidate_subset
        )
