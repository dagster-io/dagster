import datetime
from abc import ABC, abstractmethod
from typing import TYPE_CHECKING, Any, Mapping, NamedTuple, Optional, Sequence, Union

import pendulum

from dagster._annotations import experimental
from dagster._core.asset_graph_view.asset_graph_view import AssetSlice, TemporalContext
from dagster._core.definitions.asset_key import AssetKey
from dagster._core.definitions.asset_subset import AssetSubset
from dagster._core.definitions.declarative_automation.serialized_objects import (
    AssetConditionEvaluation,
    AssetConditionSnapshot,
    AssetSubsetWithMetadata,
    AutomationConditionCursor,
    AutomationConditionNodeCursor,
    get_serializable_candidate_subset,
)
from dagster._core.definitions.partition import AllPartitionsSubset
from dagster._core.definitions.time_window_partitions import BaseTimeWindowPartitionsSubset
from dagster._model import DagsterModel
from dagster._utils.security import non_secure_md5_hash_str

if TYPE_CHECKING:
    from dagster._core.definitions.auto_materialize_policy import AutoMaterializePolicy

    from .automation_context import AutomationContext
    from .operands import (
        CronTickPassedCondition,
        FailedAutomationCondition,
        InLatestTimeWindowCondition,
        InProgressAutomationCondition,
        MissingAutomationCondition,
        NewlyRequestedCondition,
        NewlyUpdatedCondition,
        WillBeRequestedCondition,
    )
    from .operators import (
        AllDepsCondition,
        AndAssetCondition,
        AnyDepsCondition,
        NewlyTrueCondition,
        NotAssetCondition,
        OrAssetCondition,
        SinceCondition,
    )


@experimental
class AutomationCondition(ABC, DagsterModel):
    @property
    def requires_cursor(self) -> bool:
        return False

    @property
    def children(self) -> Sequence["AutomationCondition"]:
        return []

    @property
    @abstractmethod
    def description(self) -> str:
        raise NotImplementedError()

    def get_snapshot(self, unique_id: str) -> AssetConditionSnapshot:
        """Returns a snapshot of this condition that can be used for serialization."""
        return AssetConditionSnapshot(
            class_name=self.__class__.__name__,
            description=self.description,
            unique_id=unique_id,
        )

    def get_unique_id(self, *, parent_unique_id: Optional[str], index: Optional[int]) -> str:
        """Returns a unique identifier for this condition within the broader condition tree."""
        parts = [str(parent_unique_id), str(index), self.__class__.__name__, self.description]
        return non_secure_md5_hash_str("".join(parts).encode())

    def as_auto_materialize_policy(self) -> "AutoMaterializePolicy":
        """Returns an AutoMaterializePolicy which contains this condition."""
        from dagster._core.definitions.auto_materialize_policy import AutoMaterializePolicy

        return AutoMaterializePolicy.from_automation_condition(self)

    @abstractmethod
    def evaluate(self, context: "AutomationContext") -> "AutomationResult":
        raise NotImplementedError()

    def __and__(self, other: "AutomationCondition") -> "AndAssetCondition":
        from .operators import AndAssetCondition

        # group AndAssetConditions together
        if isinstance(self, AndAssetCondition):
            return AndAssetCondition(operands=[*self.operands, other])
        return AndAssetCondition(operands=[self, other])

    def __or__(self, other: "AutomationCondition") -> "OrAssetCondition":
        from .operators import OrAssetCondition

        # group OrAssetConditions together
        if isinstance(self, OrAssetCondition):
            return OrAssetCondition(operands=[*self.operands, other])
        return OrAssetCondition(operands=[self, other])

    def __invert__(self) -> "NotAssetCondition":
        from .operators import NotAssetCondition

        return NotAssetCondition(operand=self)

    def since(self, reset_condition: "AutomationCondition") -> "SinceCondition":
        """Returns a AutomationCondition that is true if this condition has become true since the
        last time the reference condition became true.
        """
        from .operators import SinceCondition

        return SinceCondition(trigger_condition=self, reset_condition=reset_condition)

    def newly_true(self) -> "NewlyTrueCondition":
        """Returns a AutomationCondition that is true only on the tick that this condition goes
        from false to true for a given asset partition.
        """
        from .operators import NewlyTrueCondition

        return NewlyTrueCondition(operand=self)

    @staticmethod
    def any_deps_match(condition: "AutomationCondition") -> "AnyDepsCondition":
        """Returns a AutomationCondition that is true for an asset partition if at least one partition
        of any of its dependencies evaluate to True for the given condition.

        Args:
            condition (AutomationCondition): The AutomationCondition that will be evaluated against
                this asset's dependencies.
        """
        from .operators import AnyDepsCondition

        return AnyDepsCondition(operand=condition)

    @staticmethod
    def all_deps_match(condition: "AutomationCondition") -> "AllDepsCondition":
        """Returns a AutomationCondition that is true for an asset partition if at least one partition
        of all of its dependencies evaluate to True for the given condition.

        Args:
            condition (AutomationCondition): The AutomationCondition that will be evaluated against
                this asset's dependencies.
        """
        from .operators import AllDepsCondition

        return AllDepsCondition(operand=condition)

    @staticmethod
    def missing() -> "MissingAutomationCondition":
        """Returns a AutomationCondition that is true for an asset partition if it has never been
        materialized or observed.
        """
        from .operands import MissingAutomationCondition

        return MissingAutomationCondition()

    @staticmethod
    def in_progress() -> "InProgressAutomationCondition":
        """Returns a AutomationCondition that is true for an asset partition if it is part of an in-progress run."""
        from .operands import InProgressAutomationCondition

        return InProgressAutomationCondition()

    @staticmethod
    def failed() -> "FailedAutomationCondition":
        """Returns a AutomationCondition that is true for an asset partition if its latest run failed."""
        from .operands import FailedAutomationCondition

        return FailedAutomationCondition()

    @staticmethod
    def in_latest_time_window(
        lookback_delta: Optional[datetime.timedelta] = None,
    ) -> "InLatestTimeWindowCondition":
        """Returns a AutomationCondition that is true for an asset partition when it is within the latest
        time window.

        Args:
            lookback_delta (Optional, datetime.timedelta): If provided, the condition will
                return all partitions within the provided delta of the end of the latest time window.
                For example, if this is used on a daily-partitioned asset with a lookback_delta of
                48 hours, this will return the latest two partitions.
        """
        from .operands import InLatestTimeWindowCondition

        return InLatestTimeWindowCondition.from_lookback_delta(lookback_delta)

    @staticmethod
    def will_be_requested() -> "WillBeRequestedCondition":
        """Returns a AutomationCondition that is true for an asset partition if it will be requested this tick."""
        from .operands import WillBeRequestedCondition

        return WillBeRequestedCondition()

    @staticmethod
    def newly_updated() -> "NewlyUpdatedCondition":
        """Returns a AutomationCondition that is true for an asset partition if it has been updated since the previous tick."""
        from .operands import NewlyUpdatedCondition

        return NewlyUpdatedCondition()

    @staticmethod
    def newly_requested() -> "NewlyRequestedCondition":
        """Returns a AutomationCondition that is true for an asset partition if it was requested on the previous tick."""
        from .operands import NewlyRequestedCondition

        return NewlyRequestedCondition()

    @staticmethod
    def cron_tick_passed(
        cron_schedule: str, cron_timezone: str = "UTC"
    ) -> "CronTickPassedCondition":
        """Returns a AutomationCondition that is true for all asset partitions whenever a cron tick of the provided schedule is passed."""
        from .operands import CronTickPassedCondition

        return CronTickPassedCondition(cron_schedule=cron_schedule, cron_timezone=cron_timezone)

    @staticmethod
    def eager() -> "AutomationCondition":
        """Returns a condition which will "eagerly" fill in missing partitions as they are created,
        and ensures unpartitioned assets are updated whenever their dependencies are updated (either
        via scheduled execution or ad-hoc runs).

        Specifically, this is a composite AutomationCondition which is true for an asset partition
        if all of the following are true:

        - The asset partition is within the latest time window
        - At least one of its parents has been updated more recently than it has been requested, or
            the asset partition has never been materialized
        - None of its parent partitions are missing
        - None of its parent partitions are currently part of an in-progress run
        """
        became_missing_or_any_deps_updated = (
            AutomationCondition.missing().newly_true()
            | AutomationCondition.any_deps_match(
                AutomationCondition.newly_updated() | AutomationCondition.will_be_requested()
            )
        )

        any_parent_missing = AutomationCondition.any_deps_match(
            AutomationCondition.missing() & ~AutomationCondition.will_be_requested()
        )
        any_parent_in_progress = AutomationCondition.any_deps_match(
            AutomationCondition.in_progress()
        )
        return (
            AutomationCondition.in_latest_time_window()
            & became_missing_or_any_deps_updated.since(
                AutomationCondition.newly_requested() | AutomationCondition.newly_updated()
            )
            & ~any_parent_missing
            & ~any_parent_in_progress
            & ~AutomationCondition.in_progress()
        )

    @staticmethod
    def cron(cron_schedule: str, cron_timezone: str = "UTC") -> "AutomationCondition":
        """Returns a condition which will materialize asset partitions within the latest time window
        on a given cron schedule, after their parents have been updated. For example, if the
        cron_schedule is set to "0 0 * * *" (every day at midnight), then this rule will not become
        true on a given day until all of its parents have been updated during that same day.

        Specifically, this is a composite AutomationCondition which is true for an asset partition
        if all of the following are true:

        - The asset partition is within the latest time window
        - All parent asset partitions have been updated since the latest tick of the provided cron
            schedule, or will be requested this tick
        - The asset partition has not been requested since the latest tick of the provided cron schedule
        """
        cron_tick_passed = AutomationCondition.cron_tick_passed(cron_schedule, cron_timezone)
        all_deps_updated_since_cron = AutomationCondition.all_deps_match(
            AutomationCondition.newly_updated().since(cron_tick_passed)
            | AutomationCondition.will_be_requested()
        )
        return (
            AutomationCondition.in_latest_time_window()
            & cron_tick_passed.since(AutomationCondition.newly_requested())
            & all_deps_updated_since_cron
        )


class AutomationResult(NamedTuple):
    condition: AutomationCondition
    condition_unique_id: str
    value_hash: str

    start_timestamp: float
    end_timestamp: float

    temporal_context: TemporalContext

    true_slice: AssetSlice
    candidate_slice: AssetSlice

    child_results: Sequence["AutomationResult"]

    node_cursor: Optional[AutomationConditionNodeCursor]
    serializable_evaluation: AssetConditionEvaluation

    extra_state: Any
    subsets_with_metadata: Sequence[AssetSubsetWithMetadata]

    @property
    def asset_key(self) -> AssetKey:
        return self.true_slice.asset_key

    @property
    def true_subset(self) -> AssetSubset:
        return self.true_slice.convert_to_valid_asset_subset()

    @staticmethod
    def _create(
        context: "AutomationContext",
        true_slice: AssetSlice,
        subsets_with_metadata: Sequence[AssetSubsetWithMetadata],
        extra_state: Optional[Union[AssetSubset, Sequence[AssetSubset]]],
        child_results: Sequence["AutomationResult"],
    ) -> "AutomationResult":
        start_timestamp = context.create_time.timestamp()
        end_timestamp = pendulum.now("UTC").timestamp()

        return AutomationResult(
            condition=context.condition,
            condition_unique_id=context.condition_unique_id,
            value_hash=_compute_value_hash(
                condition_unique_id=context.condition_unique_id,
                condition_description=context.condition.description,
                true_slice=true_slice,
                candidate_slice=context.candidate_slice,
                subsets_with_metadata=subsets_with_metadata,
                child_results=child_results,
            ),
            start_timestamp=start_timestamp,
            end_timestamp=end_timestamp,
            temporal_context=context.new_temporal_context,
            true_slice=true_slice,
            candidate_slice=context.candidate_slice,
            subsets_with_metadata=[],
            child_results=child_results,
            extra_state=None,
            node_cursor=_create_node_cursor(
                true_slice=true_slice,
                candidate_slice=context.candidate_slice,
                subsets_with_metadata=subsets_with_metadata,
                extra_state=extra_state,
            )
            if context.condition.requires_cursor
            else None,
            serializable_evaluation=_create_serializable_evaluation(
                context=context,
                true_slice=true_slice,
                candidate_slice=context.candidate_slice,
                subsets_with_metadata=subsets_with_metadata,
                start_timestamp=start_timestamp,
                end_timestamp=end_timestamp,
                child_results=child_results,
            ),
        )

    @staticmethod
    def create_from_children(
        context: "AutomationContext",
        true_slice: AssetSlice,
        child_results: Sequence["AutomationResult"],
        extra_state: Optional[Union[AssetSubset, Sequence[AssetSubset]]] = None,
    ) -> "AutomationResult":
        """Returns a new AssetConditionEvaluation from the given child results."""
        return AutomationResult._create(
            context=context,
            true_slice=true_slice,
            subsets_with_metadata=[],
            extra_state=extra_state,
            child_results=child_results,
        )

    @staticmethod
    def create(
        context: "AutomationContext",
        true_slice: AssetSlice,
        subsets_with_metadata: Sequence[AssetSubsetWithMetadata] = [],
        extra_state: Optional[Union[AssetSubset, Sequence[AssetSubset]]] = None,
    ) -> "AutomationResult":
        """Returns a new AssetConditionEvaluation from the given parameters."""
        return AutomationResult._create(
            context=context,
            true_slice=true_slice,
            subsets_with_metadata=subsets_with_metadata,
            extra_state=extra_state,
            child_results=[],
        )

    def get_child_node_cursors(self) -> Mapping[str, AutomationConditionNodeCursor]:
        node_cursors = {self.condition_unique_id: self.node_cursor} if self.node_cursor else {}
        for child_result in self.child_results:
            node_cursors.update(child_result.get_child_node_cursors())
        return node_cursors

    def get_new_cursor(self) -> AutomationConditionCursor:
        return AutomationConditionCursor(
            previous_requested_subset=self.serializable_evaluation.true_subset,
            effective_timestamp=self.temporal_context.effective_dt.timestamp(),
            last_event_id=self.temporal_context.last_event_id,
            node_cursors_by_unique_id=self.get_child_node_cursors(),
            result_value_hash=self.value_hash,
        )


def _create_node_cursor(
    true_slice: AssetSlice,
    candidate_slice: AssetSlice,
    subsets_with_metadata: Sequence[AssetSubsetWithMetadata],
    extra_state: Optional[Union[AssetSubset, Sequence[AssetSubset]]],
) -> AutomationConditionNodeCursor:
    return AutomationConditionNodeCursor(
        true_subset=true_slice.convert_to_valid_asset_subset(),
        candidate_subset=get_serializable_candidate_subset(
            candidate_slice.convert_to_valid_asset_subset()
        ),
        subsets_with_metadata=subsets_with_metadata,
        extra_state=extra_state,
    )


def _create_serializable_evaluation(
    context: "AutomationContext",
    true_slice: AssetSlice,
    candidate_slice: AssetSlice,
    subsets_with_metadata: Sequence[AssetSubsetWithMetadata],
    start_timestamp: float,
    end_timestamp: float,
    child_results: Sequence[AutomationResult],
) -> AssetConditionEvaluation:
    return AssetConditionEvaluation(
        condition_snapshot=context.condition.get_snapshot(context.condition_unique_id),
        true_subset=true_slice.convert_to_valid_asset_subset(),
        candidate_subset=get_serializable_candidate_subset(
            candidate_slice.convert_to_valid_asset_subset()
        ),
        subsets_with_metadata=subsets_with_metadata,
        start_timestamp=start_timestamp,
        end_timestamp=end_timestamp,
        child_evaluations=[child_result.serializable_evaluation for child_result in child_results],
    )


def _compute_value_hash(
    condition_unique_id: str,
    condition_description: str,
    true_slice: AssetSlice,
    candidate_slice: AssetSlice,
    subsets_with_metadata: Sequence[AssetSubsetWithMetadata],
    child_results: Sequence[AutomationResult],
) -> str:
    """Computes a unique hash representing the values contained within an evaluation result. This
    string will be identical for results which have identical values, allowing us to detect changes
    without serializing the entire value.
    """
    components: Sequence[str] = [
        condition_unique_id,
        condition_description,
        _compute_subset_value_str(true_slice.convert_to_valid_asset_subset()),
        _compute_subset_value_str(candidate_slice.convert_to_valid_asset_subset()),
        *(_compute_subset_with_metadata_value_str(swm) for swm in subsets_with_metadata),
        *(child_result.value_hash for child_result in child_results),
    ]
    return non_secure_md5_hash_str("".join(components).encode("utf-8"))


def _compute_subset_value_str(subset: AssetSubset) -> str:
    """Computes a unique string representing a given AssetSubsets. This string will be equal for
    equivalent AssetSubsets.
    """
    if isinstance(subset.value, bool):
        return str(subset.value)
    elif isinstance(subset.value, AllPartitionsSubset):
        return AllPartitionsSubset.__name__
    elif isinstance(subset.value, BaseTimeWindowPartitionsSubset):
        return str(
            [
                (tw.start.timestamp(), tw.end.timestamp())
                for tw in sorted(subset.value.included_time_windows)
            ]
        )
    else:
        return str(list(sorted(subset.asset_partitions)))


def _compute_subset_with_metadata_value_str(subset_with_metadata: AssetSubsetWithMetadata):
    return _compute_subset_value_str(subset_with_metadata.subset) + str(
        sorted(subset_with_metadata.frozen_metadata)
    )
