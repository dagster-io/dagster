from collections.abc import Iterator, Mapping, Sequence
from dataclasses import dataclass
from typing import (  # noqa: UP035
    TYPE_CHECKING,
    AbstractSet,
    Generic,
    NamedTuple,
    Optional,
    TypeVar,
    Union,
)

from dagster_shared.serdes import whitelist_for_serdes

from dagster._core.asset_graph_view.asset_graph_view import TemporalContext
from dagster._core.asset_graph_view.serializable_entity_subset import SerializableEntitySubset
from dagster._core.definitions.asset_key import T_EntityKey
from dagster._core.definitions.events import AssetKey
from dagster._core.definitions.metadata import MetadataMapping, MetadataValue
from dagster._core.definitions.partition import AllPartitionsSubset
from dagster._record import record
from dagster._time import datetime_from_timestamp

if TYPE_CHECKING:
    from dagster._core.definitions.declarative_automation.automation_condition import (
        AutomationResult,
    )
    from dagster._core.definitions.declarative_automation.automation_context import (
        AutomationContext,
    )

StructuredCursor = Union[str, SerializableEntitySubset, Sequence[SerializableEntitySubset]]
T_StructuredCursor = TypeVar("T_StructuredCursor", bound=StructuredCursor)


@whitelist_for_serdes
@record(checked=False)
class HistoricalAllPartitionsSubsetSentinel:
    """Serializable indicator that this value was an AllPartitionsSubset at serialization time, but
    the partitions may have changed since that time.
    """


def get_serializable_candidate_subset(
    candidate_subset: Union[SerializableEntitySubset, HistoricalAllPartitionsSubsetSentinel],
) -> Union[SerializableEntitySubset, HistoricalAllPartitionsSubsetSentinel]:
    """Do not serialize the candidate subset directly if it is an AllPartitionsSubset."""
    if isinstance(candidate_subset, SerializableEntitySubset) and isinstance(
        candidate_subset.value, AllPartitionsSubset
    ):
        return HistoricalAllPartitionsSubsetSentinel()
    return candidate_subset


@whitelist_for_serdes(storage_name="AssetConditionSnapshot")
class AutomationConditionNodeSnapshot(NamedTuple):
    """A serializable snapshot of a node in the AutomationCondition tree."""

    class_name: str
    description: str
    unique_id: str
    label: Optional[str] = None
    name: Optional[str] = None


@whitelist_for_serdes
class AutomationConditionSnapshot(NamedTuple):
    """A serializable snapshot of an entire AutomationCondition tree."""

    node_snapshot: AutomationConditionNodeSnapshot
    children: Sequence["AutomationConditionSnapshot"]


@whitelist_for_serdes
class AssetSubsetWithMetadata(NamedTuple):
    """An asset subset with metadata that corresponds to it."""

    subset: SerializableEntitySubset
    metadata: MetadataMapping

    @property
    def frozen_metadata(self) -> frozenset[tuple[str, MetadataValue]]:
        return frozenset(self.metadata.items())


@whitelist_for_serdes(storage_name="AssetConditionEvaluation")
@dataclass
class AutomationConditionEvaluation(Generic[T_EntityKey]):
    """Serializable representation of the results of evaluating a node in the evaluation tree."""

    condition_snapshot: AutomationConditionNodeSnapshot
    start_timestamp: Optional[float]
    end_timestamp: Optional[float]

    true_subset: SerializableEntitySubset[T_EntityKey]
    candidate_subset: Union[
        SerializableEntitySubset[T_EntityKey], HistoricalAllPartitionsSubsetSentinel
    ]
    subsets_with_metadata: Sequence[AssetSubsetWithMetadata]

    child_evaluations: Sequence["AutomationConditionEvaluation"]

    @property
    def key(self) -> T_EntityKey:
        return self.true_subset.key

    def for_child(self, child_unique_id: str) -> Optional["AutomationConditionEvaluation"]:
        """Returns the evaluation of a given child condition by finding the child evaluation that
        has an identical hash to the given condition.
        """
        for child_evaluation in self.child_evaluations:
            if child_evaluation.condition_snapshot.unique_id == child_unique_id:
                return child_evaluation

        return None

    def with_run_ids(self, run_ids: AbstractSet[str]) -> "AutomationConditionEvaluationWithRunIds":
        return AutomationConditionEvaluationWithRunIds(evaluation=self, run_ids=frozenset(run_ids))

    def iter_nodes(self) -> Iterator["AutomationConditionEvaluation"]:
        """Convenience utility for iterating through all nodes in an evaluation tree."""
        yield self
        for evaluation in self.child_evaluations:
            yield from evaluation.iter_nodes()


@whitelist_for_serdes(storage_name="AssetConditionEvaluationWithRunIds")
@dataclass
class AutomationConditionEvaluationWithRunIds(Generic[T_EntityKey]):
    """A union of an AutomatConditionEvaluation and the set of run IDs that have been launched in
    response to it.
    """

    evaluation: AutomationConditionEvaluation[T_EntityKey]
    run_ids: frozenset[str]

    @property
    def key(self) -> T_EntityKey:
        return self.evaluation.key

    @property
    def num_requested(self) -> int:
        return self.evaluation.true_subset.size


@whitelist_for_serdes
@dataclass
class AutomationConditionNodeCursor(Generic[T_EntityKey]):
    true_subset: SerializableEntitySubset[T_EntityKey]
    candidate_subset: Union[
        SerializableEntitySubset[T_EntityKey], HistoricalAllPartitionsSubsetSentinel
    ]
    subsets_with_metadata: Sequence[AssetSubsetWithMetadata]
    extra_state: Optional[StructuredCursor]

    def get_structured_cursor(
        self, as_type: type[T_StructuredCursor]
    ) -> Optional[T_StructuredCursor]:
        """Returns the extra_state value if it is of the expected type. Otherwise, returns None."""
        if isinstance(self.extra_state, as_type):
            return self.extra_state
        return None


@whitelist_for_serdes
@dataclass
class AutomationConditionCursor(Generic[T_EntityKey]):
    """Incremental state calculated during the evaluation of a AutomationCondition. This may be used
    on the subsequent evaluation to make the computation more efficient.

    Args:
        previous_requested_subset: The subset that was requested for this asset on the previous tick.
        effective_timestamp: The timestamp at which the evaluation was performed.
        last_event_id: The maximum storage ID over all events used in this evaluation.
        node_cursors_by_unique_id: A mapping from the unique ID of each condition in the evaluation
            tree to any incremental state calculated for it.
        result_hash: A unique hash of the result for this tick. Used to determine if anything
            has changed since the last time this was evaluated.
    """

    previous_requested_subset: SerializableEntitySubset
    effective_timestamp: float
    last_event_id: Optional[int]

    node_cursors_by_unique_id: Mapping[str, AutomationConditionNodeCursor]
    result_value_hash: str

    @staticmethod
    def backcompat_from_evaluation_state(
        evaluation_state: "AutomationConditionEvaluationState",
    ) -> "AutomationConditionCursor":
        """Serves as a temporary method to convert from old representation to the new representation."""

        def _get_node_cursors(
            evaluation: AutomationConditionEvaluation,
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
            previous_requested_subset=result.true_subset.convert_to_serializable_subset(),
            effective_timestamp=context.evaluation_time.timestamp(),
            last_event_id=context.max_storage_id,
            node_cursors_by_unique_id=_gather_node_cursors(result),
            result_value_hash=result_hash,
        )

    @property
    def key(self) -> T_EntityKey:
        return self.previous_requested_subset.key

    @property
    def temporal_context(self) -> TemporalContext:
        return TemporalContext(
            effective_dt=datetime_from_timestamp(self.effective_timestamp),
            last_event_id=self.last_event_id,
        )


@whitelist_for_serdes(storage_name="AssetConditionEvaluationState")
@dataclass(frozen=True)
class AutomationConditionEvaluationState:
    """DEPRECATED: exists only for backcompat purposes."""

    previous_evaluation: AutomationConditionEvaluation
    previous_tick_evaluation_timestamp: Optional[float]

    max_storage_id: Optional[int]
    extra_state_by_unique_id: Mapping[str, Optional[StructuredCursor]]

    @property
    def asset_key(self) -> AssetKey:
        return self.previous_evaluation.key

    @property
    def true_subset(self) -> SerializableEntitySubset:
        return self.previous_evaluation.true_subset
