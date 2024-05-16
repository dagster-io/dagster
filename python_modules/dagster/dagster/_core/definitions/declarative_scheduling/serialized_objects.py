from dataclasses import dataclass
from typing import (
    TYPE_CHECKING,
    AbstractSet,
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

from dagster._core.definitions.asset_subset import AssetSubset, ValidAssetSubset
from dagster._core.definitions.events import AssetKey
from dagster._core.definitions.metadata import MetadataMapping, MetadataValue
from dagster._core.definitions.partition import AllPartitionsSubset
from dagster._model import DagsterModel
from dagster._serdes.serdes import whitelist_for_serdes

if TYPE_CHECKING:
    from dagster._core.definitions.declarative_scheduling.scheduling_condition import (
        SchedulingResult,
    )
    from dagster._core.definitions.declarative_scheduling.scheduling_context import (
        SchedulingContext,
    )

T = TypeVar("T")


@whitelist_for_serdes
class HistoricalAllPartitionsSubsetSentinel(DagsterModel):
    """Serializable indicator that this value was an AllPartitionsSubset at serialization time, but
    the partitions may have changed since that time.
    """


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
    def from_result(result: "SchedulingResult") -> "AssetConditionEvaluation":
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
    extra_state_by_unique_id: Mapping[str, Optional[Union[AssetSubset, Sequence[AssetSubset]]]]

    @property
    def asset_key(self) -> AssetKey:
        return self.previous_evaluation.asset_key

    @property
    def true_subset(self) -> AssetSubset:
        return self.previous_evaluation.true_subset

    @staticmethod
    def create(
        context: "SchedulingContext", root_result: "SchedulingResult"
    ) -> "AssetConditionEvaluationState":
        """Convenience constructor to generate an AssetConditionEvaluationState from the root result
        and the context in which it was evaluated.
        """

        # flatten the extra state into a single dict
        def _flatten_extra_state(
            r: "SchedulingResult",
        ) -> Mapping[str, Optional[Union[AssetSubset, Sequence[AssetSubset]]]]:
            extra_state: Dict[str, Optional[Union[AssetSubset, Sequence[AssetSubset]]]] = (
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
