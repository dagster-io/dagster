from dataclasses import dataclass
from typing import (
    TYPE_CHECKING,
    AbstractSet,
    FrozenSet,
    Mapping,
    NamedTuple,
    Optional,
    Sequence,
    Tuple,
    Type,
    TypeVar,
    Union,
)

from dagster._core.asset_graph_view.asset_graph_view import TemporalContext
from dagster._core.definitions.asset_subset import AssetSubset
from dagster._core.definitions.events import AssetKey
from dagster._core.definitions.metadata import MetadataMapping, MetadataValue
from dagster._core.definitions.partition import AllPartitionsSubset
from dagster._model.decorator import dagster_model
from dagster._serdes.serdes import whitelist_for_serdes
from dagster._utils import utc_datetime_from_timestamp

if TYPE_CHECKING:
    from dagster._core.definitions.declarative_automation.automation_condition import (
        AutomationResult,
    )
    from dagster._core.definitions.declarative_automation.automation_context import (
        AutomationContext,
    )

T = TypeVar("T")


@whitelist_for_serdes
@dagster_model(checked=False)
class HistoricalAllPartitionsSubsetSentinel:
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
class AssetConditionSnapshot(NamedTuple):
    """A serializable snapshot of a node in the AutomationCondition tree."""

    class_name: str
    description: str
    unique_id: str


@whitelist_for_serdes
class AssetSubsetWithMetadata(NamedTuple):
    """An asset subset with metadata that corresponds to it."""

    subset: AssetSubset
    metadata: MetadataMapping

    @property
    def frozen_metadata(self) -> FrozenSet[Tuple[str, MetadataValue]]:
        return frozenset(self.metadata.items())


@whitelist_for_serdes
class AssetConditionEvaluation(NamedTuple):
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
class AssetConditionEvaluationWithRunIds(NamedTuple):
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


@whitelist_for_serdes
class AutomationConditionNodeCursor(NamedTuple):
    true_subset: AssetSubset
    candidate_subset: Union[AssetSubset, HistoricalAllPartitionsSubsetSentinel]
    subsets_with_metadata: Sequence[AssetSubsetWithMetadata]
    extra_state: Optional[Union[AssetSubset, Sequence[AssetSubset]]]

    def get_extra_state(self, as_type: Type[T]) -> Optional[T]:
        """Returns the extra_state value if it is of the expected type. Otherwise, returns None."""
        if isinstance(self.extra_state, as_type):
            return self.extra_state
        return None


@whitelist_for_serdes
class AutomationConditionCursor(NamedTuple):
    """Incremental state calculated during the evaluation of a AutomationCondition. This may be used
    on the subsequent evaluation to make the computation more efficient.

    Attributes:
        previous_requested_subset: The subset that was requested for this asset on the previous tick.
        effective_timestamp: The timestamp at which the evaluation was performed.
        last_event_id: The maximum storage ID over all events used in this evaluation.
        node_cursors_by_unique_id: A mapping from the unique ID of each condition in the evaluation
            tree to any incremental state calculated for it.
        result_hash: A unique hash of the result for this tick. Used to determine if anything
            has changed since the last time this was evaluated.
    """

    previous_requested_subset: AssetSubset
    effective_timestamp: float
    last_event_id: Optional[int]

    node_cursors_by_unique_id: Mapping[str, AutomationConditionNodeCursor]
    result_value_hash: str

    @staticmethod
    def backcompat_from_evaluation_state(
        evaluation_state: AssetConditionEvaluationState,
    ) -> "AutomationConditionCursor":
        """Serves as a temporary method to convert from old representation to the new representation."""

        def _get_node_cursors(
            evaluation: AssetConditionEvaluation,
        ) -> Mapping[str, AutomationConditionNodeCursor]:
            node_cursors = {
                evaluation.condition_snapshot.unique_id: AutomationConditionNodeCursor(
                    true_subset=evaluation.true_subset,
                    candidate_subset=evaluation.candidate_subset,
                    subsets_with_metadata=evaluation.subsets_with_metadata,
                    extra_state=evaluation_state.extra_state_by_unique_id.get(
                        evaluation.condition_snapshot.unique_id
                    ),
                )
            }
            for child in evaluation.child_evaluations:
                node_cursors.update(_get_node_cursors(child))

            return node_cursors

        return AutomationConditionCursor(
            previous_requested_subset=evaluation_state.previous_evaluation.true_subset,
            effective_timestamp=evaluation_state.previous_tick_evaluation_timestamp or 0,
            last_event_id=evaluation_state.max_storage_id,
            node_cursors_by_unique_id=_get_node_cursors(evaluation_state.previous_evaluation),
            result_value_hash="",
        )

    @staticmethod
    def from_result(
        context: "AutomationContext", result: "AutomationResult", result_hash: str
    ) -> "AutomationConditionCursor":
        def _gather_node_cursors(r: "AutomationResult"):
            node_cursors = {r.condition_unique_id: r.node_cursor} if r.node_cursor else {}
            for rr in r.child_results:
                node_cursors.update(_gather_node_cursors(rr))
            return node_cursors

        return AutomationConditionCursor(
            previous_requested_subset=result.true_subset,
            effective_timestamp=context.effective_dt.timestamp(),
            last_event_id=context.new_max_storage_id,
            node_cursors_by_unique_id=_gather_node_cursors(result),
            result_value_hash=result_hash,
        )

    @property
    def asset_key(self) -> AssetKey:
        return self.previous_requested_subset.asset_key

    @property
    def temporal_context(self) -> TemporalContext:
        return TemporalContext(
            effective_dt=utc_datetime_from_timestamp(self.effective_timestamp),
            last_event_id=self.last_event_id,
        )
