import datetime
from abc import ABC, abstractmethod
from typing import TYPE_CHECKING, Any, Mapping, NamedTuple, Optional, Sequence, Union

import pytz

from dagster._annotations import experimental
from dagster._core.asset_graph_view.asset_graph_view import AssetSlice, TemporalContext
from dagster._core.definitions.asset_key import AssetKey
from dagster._core.definitions.asset_selection import AssetSelection
from dagster._core.definitions.asset_subset import AssetSubset
from dagster._core.definitions.declarative_scheduling.serialized_objects import (
    AssetConditionEvaluation,
    AssetConditionSnapshot,
    AssetSubsetWithMetadata,
    SchedulingConditionCursor,
    SchedulingConditionNodeCursor,
    get_serializable_candidate_subset,
)
from dagster._core.definitions.partition import AllPartitionsSubset
from dagster._core.definitions.time_window_partitions import BaseTimeWindowPartitionsSubset
from dagster._model import DagsterModel
from dagster._utils.security import non_secure_md5_hash_str

if TYPE_CHECKING:
    from dagster._core.definitions.auto_materialize_policy import AutoMaterializePolicy

    from .operands import (
        CronTickPassedCondition,
        FailedSchedulingCondition,
        InLatestTimeWindowCondition,
        InProgressSchedulingCondition,
        MissingSchedulingCondition,
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
    from .scheduling_context import SchedulingContext


@experimental
class SchedulingCondition(ABC, DagsterModel):
    @property
    def requires_cursor(self) -> bool:
        return False

    @property
    def children(self) -> Sequence["SchedulingCondition"]:
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

        return AutoMaterializePolicy.from_scheduling_condition(self)

    @abstractmethod
    def evaluate(self, context: "SchedulingContext") -> "SchedulingResult":
        raise NotImplementedError()

    def __and__(self, other: "SchedulingCondition") -> "AndAssetCondition":
        from .operators import AndAssetCondition

        # group AndAssetConditions together
        if isinstance(self, AndAssetCondition):
            return AndAssetCondition(operands=[*self.operands, other])
        return AndAssetCondition(operands=[self, other])

    def __or__(self, other: "SchedulingCondition") -> "OrAssetCondition":
        from .operators import OrAssetCondition

        # group OrAssetConditions together
        if isinstance(self, OrAssetCondition):
            return OrAssetCondition(operands=[*self.operands, other])
        return OrAssetCondition(operands=[self, other])

    def __invert__(self) -> "NotAssetCondition":
        from .operators import NotAssetCondition

        return NotAssetCondition(operand=self)

    def since(self, reset_condition: "SchedulingCondition") -> "SinceCondition":
        """Returns a SchedulingCondition that is true if this condition has become true since the
        last time the reference condition became true.
        """
        from .operators import SinceCondition

        return SinceCondition(trigger_condition=self, reset_condition=reset_condition)

    def since_last_updated(self) -> "SinceCondition":
        """Returns a SchedulingCondition that is true if this condition has become true since the
        last time this asset was updated.
        """
        from .operands import NewlyUpdatedCondition
        from .operators import SinceCondition

        return SinceCondition(trigger_condition=self, reset_condition=NewlyUpdatedCondition())

    def since_last_requested(self) -> "SinceCondition":
        """Returns a SchedulingCondition that is true if this condition has become true since the
        last time this asset was updated.
        """
        from .operands import NewlyRequestedCondition
        from .operators import SinceCondition

        return SinceCondition(trigger_condition=self, reset_condition=NewlyRequestedCondition())

    def since_last_cron_tick(
        self, cron_schedule: str, cron_timezone: str = "UTC"
    ) -> "SinceCondition":
        """Returns a SchedulingCondition that is true if this condition has become true since the
        latest tick of the given cron schedule.
        """
        from .operands import CronTickPassedCondition
        from .operators import SinceCondition

        return SinceCondition(
            trigger_condition=self,
            reset_condition=CronTickPassedCondition(
                cron_schedule=cron_schedule, cron_timezone=cron_timezone
            ),
        )

    def newly_true(self) -> "NewlyTrueCondition":
        """Returns a SchedulingCondition that is true only on the tick that this condition goes
        from false to true for a given asset partition.
        """
        from .operators import NewlyTrueCondition

        return NewlyTrueCondition(operand=self)

    @staticmethod
    def any_deps_match(
        condition: "SchedulingCondition",
        include_selection: Optional[AssetSelection] = None,
        exclude_selection: Optional[AssetSelection] = None,
    ) -> "AnyDepsCondition":
        """Returns a SchedulingCondition that is true for an asset partition if at least one partition
        of any of its dependencies evaluate to True for the given condition.

        Args:
            condition (SchedulingCondition): The SchedulingCondition that will be evaluated against
                this asset's dependencies.
            include_selection (Optional[AssetSelection]): An AssetSelection specifying the
                dependencies which should be considered when evaluating this condition. By default,
                all dpendencies will be considered.
            exclude_selection (Optional[AssetSelection]): An AssetSelection specifying the
                dependencies which should be ignored when evaluating this condition. By default, no
                dependencies will be ignored.
        """
        from .operators import AnyDepsCondition

        return AnyDepsCondition(
            operand=condition,
            include_selection=include_selection,
            exclude_selection=exclude_selection,
        )

    @staticmethod
    def all_deps_match(
        condition: "SchedulingCondition",
        include_selection: Optional[AssetSelection] = None,
        exclude_selection: Optional[AssetSelection] = None,
    ) -> "AllDepsCondition":
        """Returns a SchedulingCondition that is true for an asset partition if at least one partition
        of all of its dependencies evaluate to True for the given condition.

        Args:
            condition (SchedulingCondition): The SchedulingCondition that will be evaluated against
                this asset's dependencies.
            include_selection (Optional[AssetSelection]): An AssetSelection specifying the
                dependencies which should be considered when evaluating this condition. By default,
                all dpendencies will be considered.
            exclude_selection (Optional[AssetSelection]): An AssetSelection specifying the
                dependencies which should be ignored when evaluating this condition. By default, no
                dependencies will be ignored.
        """
        from .operators import AllDepsCondition

        return AllDepsCondition(
            operand=condition,
            include_selection=include_selection,
            exclude_selection=exclude_selection,
        )

    @staticmethod
    def missing() -> "MissingSchedulingCondition":
        """Returns a SchedulingCondition that is true for an asset partition if it has never been
        materialized or observed.
        """
        from .operands import MissingSchedulingCondition

        return MissingSchedulingCondition()

    @staticmethod
    def in_progress() -> "InProgressSchedulingCondition":
        """Returns a SchedulingCondition that is true for an asset partition if it is part of an in-progress run."""
        from .operands import InProgressSchedulingCondition

        return InProgressSchedulingCondition()

    @staticmethod
    def failed() -> "FailedSchedulingCondition":
        """Returns a SchedulingCondition that is true for an asset partition if its latest run failed."""
        from .operands import FailedSchedulingCondition

        return FailedSchedulingCondition()

    @staticmethod
    def in_latest_time_window(
        lookback_delta: Optional[datetime.timedelta] = None,
    ) -> "InLatestTimeWindowCondition":
        """Returns a SchedulingCondition that is true for an asset partition when it is within the latest
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
        """Returns a SchedulingCondition that is true for an asset partition if it will be requested this tick."""
        from .operands import WillBeRequestedCondition

        return WillBeRequestedCondition()

    @staticmethod
    def newly_updated() -> "NewlyUpdatedCondition":
        """Returns a SchedulingCondition that is true for an asset partition if it has been updated since the previous tick."""
        from .operands import NewlyUpdatedCondition

        return NewlyUpdatedCondition()

    @staticmethod
    def newly_requested() -> "NewlyRequestedCondition":
        """Returns a SchedulingCondition that is true for an asset partition if it was requested on the previous tick."""
        from .operands import NewlyRequestedCondition

        return NewlyRequestedCondition()

    @staticmethod
    def cron_tick_passed(
        cron_schedule: str, cron_timezone: str = "UTC"
    ) -> "CronTickPassedCondition":
        """Returns a SchedulingCondition that is true for all asset partitions whenever a cron tick of the provided schedule is passed."""
        from .operands import CronTickPassedCondition

        return CronTickPassedCondition(cron_schedule=cron_schedule, cron_timezone=cron_timezone)

    @staticmethod
    def eager() -> "SchedulingCondition":
        """Returns a condition which will "eagerly" fill in missing partitions as they are created,
        and ensures unpartitioned assets are updated whenever their dependencies are updated (either
        via scheduled execution or ad-hoc runs).

        Specifically, this is a composite SchedulingCondition which is true for an asset partition
        if all of the following are true:

        - The asset partition is within the latest time window
        - At least one of its parents has been updated more recently than it has been requested, or
            the asset partition has never been materialized
        - None of its parent partitions are missing
        - None of its parent partitions are currently part of an in-progress run
        """
        became_missing_or_any_deps_updated = (
            SchedulingCondition.missing().newly_true()
            | SchedulingCondition.any_deps_match(
                SchedulingCondition.newly_updated() | SchedulingCondition.will_be_requested()
            )
        )

        any_parent_missing = SchedulingCondition.any_deps_match(
            SchedulingCondition.missing() & ~SchedulingCondition.will_be_requested()
        )
        any_parent_in_progress = SchedulingCondition.any_deps_match(
            SchedulingCondition.in_progress()
        )
        return (
            SchedulingCondition.in_latest_time_window()
            & became_missing_or_any_deps_updated.since_last_requested()
            & ~any_parent_missing
            & ~any_parent_in_progress
        )

    @staticmethod
    def on_cron(cron_schedule: str, cron_timezone: str = "UTC") -> "SchedulingCondition":
        """Returns a condition which will materialize asset partitions within the latest time window
        on a given cron schedule, after their parents have been updated. For example, if the
        cron_schedule is set to "0 0 * * *" (every day at midnight), then this rule will not become
        true on a given day until all of its parents have been updated during that same day.

        Specifically, this is a composite SchedulingCondition which is true for an asset partition
        if all of the following are true:

        - The asset partition is within the latest time window
        - All parent asset partitions have been updated since the latest tick of the provided cron
            schedule, or will be requested this tick
        - The asset partition has not been requested since the latest tick of the provided cron schedule
        """
        all_deps_updated_since_cron = SchedulingCondition.all_deps_match(
            SchedulingCondition.newly_updated().since_last_cron_tick(cron_schedule, cron_timezone)
            | SchedulingCondition.will_be_requested()
        )
        return (
            SchedulingCondition.in_latest_time_window()
            & SchedulingCondition.cron_tick_passed(
                cron_schedule, cron_timezone
            ).since_last_requested()
            & all_deps_updated_since_cron
        )


class SchedulingResult(NamedTuple):
    condition: SchedulingCondition
    condition_unique_id: str
    value_hash: str

    start_timestamp: float
    end_timestamp: float

    temporal_context: TemporalContext

    true_slice: AssetSlice
    candidate_slice: AssetSlice

    child_results: Sequence["SchedulingResult"]

    node_cursor: Optional[SchedulingConditionNodeCursor]
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
        context: "SchedulingContext",
        true_slice: AssetSlice,
        subsets_with_metadata: Sequence[AssetSubsetWithMetadata],
        extra_state: Optional[Union[AssetSubset, Sequence[AssetSubset]]],
        child_results: Sequence["SchedulingResult"],
    ) -> "SchedulingResult":
        start_timestamp = context.create_time.timestamp()
        end_timestamp = datetime.datetime.now(pytz.utc).timestamp()

        return SchedulingResult(
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
        context: "SchedulingContext",
        true_slice: AssetSlice,
        child_results: Sequence["SchedulingResult"],
        extra_state: Optional[Union[AssetSubset, Sequence[AssetSubset]]] = None,
    ) -> "SchedulingResult":
        """Returns a new AssetConditionEvaluation from the given child results."""
        return SchedulingResult._create(
            context=context,
            true_slice=true_slice,
            subsets_with_metadata=[],
            extra_state=extra_state,
            child_results=child_results,
        )

    @staticmethod
    def create(
        context: "SchedulingContext",
        true_slice: AssetSlice,
        subsets_with_metadata: Sequence[AssetSubsetWithMetadata] = [],
        extra_state: Optional[Union[AssetSubset, Sequence[AssetSubset]]] = None,
    ) -> "SchedulingResult":
        """Returns a new AssetConditionEvaluation from the given parameters."""
        return SchedulingResult._create(
            context=context,
            true_slice=true_slice,
            subsets_with_metadata=subsets_with_metadata,
            extra_state=extra_state,
            child_results=[],
        )

    def get_child_node_cursors(self) -> Mapping[str, SchedulingConditionNodeCursor]:
        node_cursors = {self.condition_unique_id: self.node_cursor} if self.node_cursor else {}
        for child_result in self.child_results:
            node_cursors.update(child_result.get_child_node_cursors())
        return node_cursors

    def get_new_cursor(self) -> SchedulingConditionCursor:
        return SchedulingConditionCursor(
            previous_requested_subset=self.true_subset,
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
) -> SchedulingConditionNodeCursor:
    return SchedulingConditionNodeCursor(
        true_subset=true_slice.convert_to_valid_asset_subset(),
        candidate_subset=get_serializable_candidate_subset(
            candidate_slice.convert_to_valid_asset_subset()
        ),
        subsets_with_metadata=subsets_with_metadata,
        extra_state=extra_state,
    )


def _create_serializable_evaluation(
    context: "SchedulingContext",
    true_slice: AssetSlice,
    candidate_slice: AssetSlice,
    subsets_with_metadata: Sequence[AssetSubsetWithMetadata],
    start_timestamp: float,
    end_timestamp: float,
    child_results: Sequence[SchedulingResult],
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
    child_results: Sequence[SchedulingResult],
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
        return str(list(sorted(subset.value.included_time_windows)))
    else:
        return str(list(sorted(subset.asset_partitions)))


def _compute_subset_with_metadata_value_str(subset_with_metadata: AssetSubsetWithMetadata):
    return _compute_subset_value_str(subset_with_metadata.subset) + str(
        sorted(subset_with_metadata.frozen_metadata)
    )
