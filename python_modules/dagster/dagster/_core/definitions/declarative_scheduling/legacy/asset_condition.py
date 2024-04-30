import datetime
from abc import ABC, abstractmethod
from dataclasses import dataclass
from typing import (
    TYPE_CHECKING,
    AbstractSet,
    Any,
    Dict,
    FrozenSet,
    Mapping,
    Optional,
    Sequence,
    Tuple,
    Type,
    TypeVar,
    Union,
)

import pendulum

from dagster._core.asset_graph_view.asset_graph_view import AssetSlice
from dagster._core.definitions.events import AssetKey
from dagster._core.definitions.metadata import MetadataMapping, MetadataValue
from dagster._core.definitions.partition import AllPartitionsSubset
from dagster._model import DagsterModel
from dagster._serdes.serdes import PackableValue, whitelist_for_serdes
from dagster._utils.security import non_secure_md5_hash_str

from ...asset_subset import AssetSubset, ValidAssetSubset
from ...auto_materialize_rule import AutoMaterializeRule

if TYPE_CHECKING:
    from ..scheduling_context import SchedulingContext


T = TypeVar("T")


@whitelist_for_serdes
class HistoricalAllPartitionsSubsetSentinel(DagsterModel):
    """Serializable indicator that this value was an AllPartitionsSubset at serialization time, but
    the partitions may have changed since that time.
    """


@whitelist_for_serdes
class AssetConditionSnapshot(DagsterModel):
    """A serializable snapshot of a node in the AutomationCondition tree."""

    class_name: str
    description: str
    unique_id: str


@whitelist_for_serdes
class AssetSubsetWithMetadata(DagsterModel):
    """An asset subset with metadata that corresponds to it."""

    subset: AssetSubset
    metadata: MetadataMapping

    @property
    def frozen_metadata(self) -> FrozenSet[Tuple[str, MetadataValue]]:
        return frozenset(self.metadata.items())


def get_serializable_candidate_subset(
    candidate_subset: Union[AssetSubset, HistoricalAllPartitionsSubsetSentinel],
) -> Union[AssetSubset, HistoricalAllPartitionsSubsetSentinel]:
    """Do not serialize the candidate subset directly if it is an AllPartitionsSubset."""
    if isinstance(candidate_subset, AssetSubset) and isinstance(
        candidate_subset.value, AllPartitionsSubset
    ):
        return HistoricalAllPartitionsSubsetSentinel()
    return candidate_subset


@whitelist_for_serdes
class AssetConditionEvaluation(DagsterModel):
    """Serializable representation of the results of evaluating a node in the evaluation tree."""

    condition_snapshot: AssetConditionSnapshot
    start_timestamp: Optional[float]
    end_timestamp: Optional[float]

    true_subset: AssetSubset
    candidate_subset: Union[AssetSubset, HistoricalAllPartitionsSubsetSentinel]
    subsets_with_metadata: Sequence[AssetSubsetWithMetadata]

    child_evaluations: Sequence["AssetConditionEvaluation"]

    @property
    def asset_key(self) -> AssetKey:
        return self.true_subset.asset_key

    @staticmethod
    def from_result(result: "AssetConditionResult") -> "AssetConditionEvaluation":
        return AssetConditionEvaluation(
            condition_snapshot=result.condition.get_snapshot(result.condition_unique_id),
            start_timestamp=result.start_timestamp,
            end_timestamp=result.end_timestamp,
            true_subset=result.true_subset,
            candidate_subset=get_serializable_candidate_subset(result.candidate_subset),
            subsets_with_metadata=result.subsets_with_metadata,
            child_evaluations=[
                AssetConditionEvaluation.from_result(child_result)
                for child_result in result.child_results
            ],
        )

    def equivalent_to_stored_evaluation(self, other: Optional["AssetConditionEvaluation"]) -> bool:
        """Returns if this evaluation is functionally equivalent to the given stored evaluation.
        This is used to determine if it is necessary to store this new evaluation in the database.
        Noteably, the timestamps on successive evaluations will always be different, so a simple
        equality check would be too strict.
        """
        return (
            other is not None
            and self.condition_snapshot == other.condition_snapshot
            and self.true_subset == other.true_subset
            # the candidate subset gets modified during serialization
            and get_serializable_candidate_subset(self.candidate_subset)
            == get_serializable_candidate_subset(other.candidate_subset)
            and self.subsets_with_metadata == other.subsets_with_metadata
            and len(self.child_evaluations) == len(other.child_evaluations)
            and all(
                self_child.equivalent_to_stored_evaluation(other_child)
                for self_child, other_child in zip(self.child_evaluations, other.child_evaluations)
            )
        )

    def discarded_subset(self) -> Optional[AssetSubset]:
        """Returns the AssetSubset representing asset partitions that were discarded during this
        evaluation. Note that 'discarding' is a deprecated concept that is only used for backwards
        compatibility.
        """
        if len(self.child_evaluations) != 3:
            return None
        not_discard_evaluation = self.child_evaluations[-1]
        discard_evaluation = not_discard_evaluation.child_evaluations[0]
        return discard_evaluation.true_subset

    def get_requested_or_discarded_subset(self) -> AssetSubset:
        discarded_subset = self.discarded_subset()
        if discarded_subset is None:
            return self.true_subset
        else:
            # the true_subset and discarded_subset were created on the same tick, so they are
            # guaranteed to be compatible with each other
            return (
                ValidAssetSubset(asset_key=self.asset_key, value=self.true_subset.value)
                | discarded_subset
            )

    def for_child(self, child_unique_id: str) -> Optional["AssetConditionEvaluation"]:
        """Returns the evaluation of a given child condition by finding the child evaluation that
        has an identical hash to the given condition.
        """
        for child_evaluation in self.child_evaluations:
            if child_evaluation.condition_snapshot.unique_id == child_unique_id:
                return child_evaluation

        return None

    def with_run_ids(self, run_ids: AbstractSet[str]) -> "AssetConditionEvaluationWithRunIds":
        return AssetConditionEvaluationWithRunIds(evaluation=self, run_ids=frozenset(run_ids))

    def legacy_num_skipped(self) -> int:
        if len(self.child_evaluations) < 2:
            return 0

        not_skip_evaluation = self.child_evaluations[-1]
        skip_evaluation = not_skip_evaluation.child_evaluations[0]
        return skip_evaluation.true_subset.size - self.legacy_num_discarded()

    def legacy_num_discarded(self) -> int:
        discarded_subset = self.discarded_subset()
        if discarded_subset is None:
            return 0
        return discarded_subset.size


@whitelist_for_serdes
@dataclass(frozen=True)
class AssetConditionEvaluationState:
    """Incremental state calculated during the evaluation of an AssetCondition. This may be used
    on the subsequent evaluation to make the computation more efficient.

    Attributes:
        previous_evaluation: The computed AssetConditionEvaluation.
        previous_tick_evaluation_timestamp: The evaluation_timestamp at which the evaluation was performed.
        max_storage_id: The maximum storage ID over all events used in this computation.
        extra_state_by_unique_id: A mapping from the unique ID of each condition in the evaluation
            tree to the extra state that was calculated for it, if any.
    """

    previous_evaluation: AssetConditionEvaluation
    previous_tick_evaluation_timestamp: Optional[float]

    max_storage_id: Optional[int]
    extra_state_by_unique_id: Mapping[str, Any]

    @property
    def asset_key(self) -> AssetKey:
        return self.previous_evaluation.asset_key

    @property
    def true_subset(self) -> AssetSubset:
        return self.previous_evaluation.true_subset

    @staticmethod
    def create(
        context: "SchedulingContext", root_result: "AssetConditionResult"
    ) -> "AssetConditionEvaluationState":
        """Convenience constructor to generate an AssetConditionEvaluationState from the root result
        and the context in which it was evaluated.
        """

        # flatten the extra state into a single dict
        def _flatten_extra_state(
            r: AssetConditionResult,
        ) -> Mapping[str, PackableValue]:
            extra_state: Dict[str, PackableValue] = (
                {r.condition_unique_id: r.extra_state} if r.extra_state else {}
            )
            for child in r.child_results:
                extra_state.update(_flatten_extra_state(child))
            return extra_state

        return AssetConditionEvaluationState(
            previous_evaluation=AssetConditionEvaluation.from_result(root_result),
            previous_tick_evaluation_timestamp=context.asset_graph_view.effective_dt.timestamp(),
            max_storage_id=context.new_max_storage_id,
            extra_state_by_unique_id=_flatten_extra_state(root_result),
        )

    def get_extra_state(self, unique_id: str, as_type: Type[T]) -> Optional[T]:
        """Returns the value from the extras dict for the given condition, if it exists and is of
        the expected type. Otherwise, returns None.
        """
        extra_state = self.extra_state_by_unique_id.get(unique_id)
        if isinstance(extra_state, as_type):
            return extra_state
        return None


@whitelist_for_serdes
class AssetConditionEvaluationWithRunIds(DagsterModel):
    """A union of an AssetConditionEvaluation and the set of run IDs that have been launched in
    response to it.
    """

    evaluation: AssetConditionEvaluation
    run_ids: FrozenSet[str]

    @property
    def asset_key(self) -> AssetKey:
        return self.evaluation.asset_key

    @property
    def num_requested(self) -> int:
        return self.evaluation.true_subset.size


class AssetCondition(ABC, DagsterModel):
    """An AssetCondition represents some state of the world that can influence if an asset
    partition should be materialized or not. AssetConditions can be combined to create
    new conditions using the `&` (and), `|` (or), and `~` (not) operators.

    Examples:
        .. code-block:: python

            from dagster import AssetCondition, AutoMaterializePolicy

            # At least one parent is newer and no parent is missing.
            my_policy = AutoMaterializePolicy(
                asset_condition = AssetCondition.parent_newer() & ~AssetCondition.parent_missing()
            )
    """

    def get_unique_id(self, parent_unique_id: Optional[str]) -> str:
        """Returns a unique identifier for this condition within the broader condition tree."""
        parts = [str(parent_unique_id), self.__class__.__name__, self.description]
        return non_secure_md5_hash_str("".join(parts).encode())

    @abstractmethod
    def evaluate(self, context: "SchedulingContext") -> "AssetConditionResult":
        raise NotImplementedError()

    @property
    @abstractmethod
    def description(self) -> str:
        raise NotImplementedError()

    def __and__(self, other: "AssetCondition") -> "AssetCondition":
        from ..operators.boolean_operators import AndAssetCondition

        # group AndAssetConditions together
        if isinstance(self, AndAssetCondition):
            return AndAssetCondition(operands=[*self.operands, other])
        return AndAssetCondition(operands=[self, other])

    def __or__(self, other: "AssetCondition") -> "AssetCondition":
        from ..operators.boolean_operators import OrAssetCondition

        # group OrAssetConditions together
        if isinstance(self, OrAssetCondition):
            return OrAssetCondition(operands=[*self.operands, other])
        return OrAssetCondition(operands=[self, other])

    def __invert__(self) -> "AssetCondition":
        from ..operators.boolean_operators import NotAssetCondition

        return NotAssetCondition(operand=self)

    @property
    def children(self) -> Sequence["AssetCondition"]:
        return []

    def get_snapshot(self, unique_id: str) -> AssetConditionSnapshot:
        """Returns a snapshot of this condition that can be used for serialization."""
        return AssetConditionSnapshot(
            class_name=self.__class__.__name__,
            description=self.description,
            unique_id=unique_id,
        )

    @staticmethod
    def parent_newer() -> "AssetCondition":
        """Returns an AssetCondition that is true for an asset partition when at least one parent
        asset partition is newer than it.
        """
        from .rule_condition import RuleCondition

        return RuleCondition(rule=AutoMaterializeRule.materialize_on_parent_updated())

    @staticmethod
    def missing() -> "AssetCondition":
        """Returns an AssetCondition that is true for an asset partition when it has never been
        materialized.
        """
        from .rule_condition import RuleCondition

        return RuleCondition(rule=AutoMaterializeRule.materialize_on_missing())

    @staticmethod
    def parent_missing() -> "AssetCondition":
        """Returns an AssetCondition that is true for an asset partition when at least one parent
        asset partition has never been materialized or observed.
        """
        from .rule_condition import RuleCondition

        return RuleCondition(rule=AutoMaterializeRule.skip_on_parent_missing())

    @staticmethod
    def updated_since_cron(cron_schedule: str, timezone: str = "UTC") -> "AssetCondition":
        """Returns an AssetCondition that is true for an asset partition when it has been updated
        since the latest tick of the given cron schedule. For partitioned assets with a time
        component, this can only be true for the most recent partition.
        """
        from .rule_condition import RuleCondition

        return ~RuleCondition(rule=AutoMaterializeRule.materialize_on_cron(cron_schedule, timezone))

    @staticmethod
    def parents_updated_since_cron(cron_schedule: str, timezone: str = "UTC") -> "AssetCondition":
        """Returns an AssetCondition that is true for an asset partition when all parent asset
        partitions have been updated more recently than the latest tick of the given cron schedule.
        """
        from .rule_condition import RuleCondition

        return ~RuleCondition(
            rule=AutoMaterializeRule.skip_on_not_all_parents_updated_since_cron(
                cron_schedule, timezone
            )
        )

    @staticmethod
    def any_deps_match(condition: "AssetCondition") -> "AssetCondition":
        """Returns an AssetCondition that is true for an asset partition if at least one partition
        of any of its dependencies evaluate to True for the given condition.
        """
        from ..operators.dep_operators import AnyDepsCondition

        return AnyDepsCondition(operand=condition)

    @staticmethod
    def all_deps_match(condition: "AssetCondition") -> "AssetCondition":
        """Returns an AssetCondition that is true for an asset partition if at least one partition
        of all of its dependencies evaluate to True for the given condition.
        """
        from ..operators.dep_operators import AllDepsCondition

        return AllDepsCondition(operand=condition)

    @staticmethod
    def missing_() -> "AssetCondition":
        """Returns an AssetCondition that is true for an asset partition when it has been materialized."""
        from ..operands.slice_conditions import MissingSchedulingCondition

        return MissingSchedulingCondition()

    @staticmethod
    def in_progress() -> "AssetCondition":
        """Returns an AssetCondition that is true for an asset partition if it is part of an in-progress run."""
        from ..operands.slice_conditions import InProgressSchedulingCondition

        return InProgressSchedulingCondition()

    @staticmethod
    def in_latest_time_window(
        lookback_delta: Optional[datetime.timedelta] = None,
    ) -> "AssetCondition":
        """Returns an AssetCondition that is true for an asset partition when it is within the latest
        time window.

        Args:
            lookback_delta (Optional, datetime.timedelta): If provided, the condition will
                return all partitions within the provided delta of the end of the latest time window.
                For example, if you provide a delta of 48 hours for a daily-partitioned asset, this
                will return the last two partitions.
        """
        from ..operands.slice_conditions import InLatestTimeWindowCondition

        return InLatestTimeWindowCondition(
            lookback_seconds=lookback_delta.total_seconds() if lookback_delta else None
        )


@dataclass(frozen=True)
class AssetConditionResult:
    condition: AssetCondition
    condition_unique_id: str
    start_timestamp: float
    end_timestamp: float

    true_slice: AssetSlice
    candidate_subset: AssetSubset
    subsets_with_metadata: Sequence[AssetSubsetWithMetadata]

    extra_state: PackableValue
    child_results: Sequence["AssetConditionResult"]

    @property
    def true_subset(self) -> AssetSubset:
        return self.true_slice.convert_to_valid_asset_subset()

    @staticmethod
    def create_from_children(
        context: "SchedulingContext",
        true_subset: ValidAssetSubset,
        child_results: Sequence["AssetConditionResult"],
    ) -> "AssetConditionResult":
        """Returns a new AssetConditionEvaluation from the given child results."""
        return AssetConditionResult(
            condition=context.condition,
            condition_unique_id=context.condition_unique_id,
            start_timestamp=context.start_timestamp,
            end_timestamp=pendulum.now("UTC").timestamp(),
            true_slice=context.asset_graph_view.get_asset_slice_from_subset(true_subset),
            candidate_subset=context.candidate_subset,
            subsets_with_metadata=[],
            child_results=child_results,
            extra_state=None,
        )

    @staticmethod
    def create(
        context: "SchedulingContext",
        true_subset: ValidAssetSubset,
        subsets_with_metadata: Sequence[AssetSubsetWithMetadata] = [],
        extra_state: PackableValue = None,
    ) -> "AssetConditionResult":
        """Returns a new AssetConditionEvaluation from the given parameters."""
        return AssetConditionResult(
            condition=context.condition,
            condition_unique_id=context.condition_unique_id,
            start_timestamp=context.start_timestamp,
            end_timestamp=pendulum.now("UTC").timestamp(),
            true_slice=context.asset_graph_view.get_asset_slice_from_subset(true_subset),
            candidate_subset=context.candidate_subset,
            subsets_with_metadata=subsets_with_metadata,
            child_results=[],
            extra_state=extra_state,
        )
