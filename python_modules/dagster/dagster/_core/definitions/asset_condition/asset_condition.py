import functools
from abc import ABC, abstractmethod
from dataclasses import dataclass
from typing import (
    TYPE_CHECKING,
    AbstractSet,
    Dict,
    FrozenSet,
    List,
    Mapping,
    Optional,
    Sequence,
    Tuple,
    Type,
    TypeVar,
    Union,
)

import pendulum

from dagster._annotations import experimental
from dagster._core.definitions.events import AssetKey
from dagster._core.definitions.metadata import MetadataMapping, MetadataValue
from dagster._core.definitions.partition import AllPartitionsSubset
from dagster._model import DagsterModel
from dagster._serdes.serdes import PackableValue, whitelist_for_serdes
from dagster._utils.security import non_secure_md5_hash_str

from ..asset_subset import AssetSubset, ValidAssetSubset
from ..auto_materialize_rule import AutoMaterializeRule

if TYPE_CHECKING:
    from .asset_condition_evaluation_context import AssetConditionEvaluationContext


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
            condition_snapshot=result.condition.snapshot,
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

    def for_child(self, child_condition: "AssetCondition") -> Optional["AssetConditionEvaluation"]:
        """Returns the evaluation of a given child condition by finding the child evaluation that
        has an identical hash to the given condition.
        """
        child_unique_id = child_condition.snapshot.unique_id
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
    extra_state_by_unique_id: Mapping[str, PackableValue]

    @property
    def asset_key(self) -> AssetKey:
        return self.previous_evaluation.asset_key

    @property
    def true_subset(self) -> AssetSubset:
        return self.previous_evaluation.true_subset

    @staticmethod
    def create(
        context: "AssetConditionEvaluationContext", root_result: "AssetConditionResult"
    ) -> "AssetConditionEvaluationState":
        """Convenience constructor to generate an AssetConditionEvaluationState from the root result
        and the context in which it was evaluated.
        """

        # flatten the extra state into a single dict
        def _flatten_extra_state(
            r: AssetConditionResult,
        ) -> Mapping[str, PackableValue]:
            extra_state: Dict[str, PackableValue] = (
                {r.condition.unique_id: r.extra_state} if r.extra_state else {}
            )
            for child in r.child_results:
                extra_state.update(_flatten_extra_state(child))
            return extra_state

        return AssetConditionEvaluationState(
            previous_evaluation=AssetConditionEvaluation.from_result(root_result),
            previous_tick_evaluation_timestamp=context.evaluation_time.timestamp(),
            max_storage_id=context.new_max_storage_id,
            extra_state_by_unique_id=_flatten_extra_state(root_result),
        )

    def get_extra_state(self, condition: "AssetCondition", as_type: Type[T]) -> Optional[T]:
        """Returns the value from the extras dict for the given condition, if it exists and is of
        the expected type. Otherwise, returns None.
        """
        extra_state = self.extra_state_by_unique_id.get(condition.unique_id)
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

    @property
    def unique_id(self) -> str:
        parts = [
            self.__class__.__name__,
            *[child.unique_id for child in self.children],
        ]
        return non_secure_md5_hash_str("".join(parts).encode())

    @abstractmethod
    def evaluate(self, context: "AssetConditionEvaluationContext") -> "AssetConditionResult":
        raise NotImplementedError()

    @property
    @abstractmethod
    def description(self) -> str:
        raise NotImplementedError()

    def __and__(self, other: "AssetCondition") -> "AssetCondition":
        # group AndAssetConditions together
        if isinstance(self, AndAssetCondition):
            return AndAssetCondition(operands=[*self.operands, other])
        return AndAssetCondition(operands=[self, other])

    def __or__(self, other: "AssetCondition") -> "AssetCondition":
        # group OrAssetConditions together
        if isinstance(self, OrAssetCondition):
            return OrAssetCondition(operands=[*self.operands, other])
        return OrAssetCondition(operands=[self, other])

    def __invert__(self) -> "AssetCondition":
        return NotAssetCondition(operand=self)

    @property
    def is_legacy(self) -> bool:
        """Returns if this condition is in the legacy format. This is used to determine if we can
        do certain types of backwards-compatible operations on it.
        """
        return (
            isinstance(self, AndAssetCondition)
            and len(self.children) in {2, 3}
            and isinstance(self.children[0], OrAssetCondition)
            and isinstance(self.children[1], NotAssetCondition)
            # the third child is the discard condition, which is optional
            and (len(self.children) == 2 or isinstance(self.children[2], NotAssetCondition))
        )

    @property
    def children(self) -> Sequence["AssetCondition"]:
        return []

    @property
    def not_skip_condition(self) -> Optional["AssetCondition"]:
        if not self.is_legacy:
            return None
        return self.children[1]

    @property
    def not_discard_condition(self) -> Optional["AssetCondition"]:
        if not self.is_legacy or not len(self.children) == 3:
            return None
        return self.children[-1]

    @functools.cached_property
    def snapshot(self) -> AssetConditionSnapshot:
        """Returns a snapshot of this condition that can be used for serialization."""
        return AssetConditionSnapshot(
            class_name=self.__class__.__name__,
            description=self.description,
            unique_id=self.unique_id,
        )

    @staticmethod
    def parent_newer() -> "AssetCondition":
        """Returns an AssetCondition that is true for an asset partition when at least one parent
        asset partition is newer than it.
        """
        return RuleCondition(rule=AutoMaterializeRule.materialize_on_parent_updated())

    @staticmethod
    def missing() -> "AssetCondition":
        """Returns an AssetCondition that is true for an asset partition when it has never been
        materialized.
        """
        from ..auto_materialize_rule import AutoMaterializeRule

        return RuleCondition(rule=AutoMaterializeRule.materialize_on_missing())

    @staticmethod
    def parent_missing() -> "AssetCondition":
        """Returns an AssetCondition that is true for an asset partition when at least one parent
        asset partition has never been materialized or observed.
        """
        from ..auto_materialize_rule import AutoMaterializeRule

        return RuleCondition(rule=AutoMaterializeRule.skip_on_parent_missing())

    @staticmethod
    def updated_since_cron(cron_schedule: str, timezone: str = "UTC") -> "AssetCondition":
        """Returns an AssetCondition that is true for an asset partition when it has been updated
        since the latest tick of the given cron schedule. For partitioned assets with a time
        component, this can only be true for the most recent partition.
        """
        from ..auto_materialize_rule import AutoMaterializeRule

        return ~RuleCondition(rule=AutoMaterializeRule.materialize_on_cron(cron_schedule, timezone))

    @staticmethod
    def parents_updated_since_cron(cron_schedule: str, timezone: str = "UTC") -> "AssetCondition":
        """Returns an AssetCondition that is true for an asset partition when all parent asset
        partitions have been updated more recently than the latest tick of the given cron schedule.
        """
        from ..auto_materialize_rule import AutoMaterializeRule

        return ~RuleCondition(
            rule=AutoMaterializeRule.skip_on_not_all_parents_updated_since_cron(
                cron_schedule, timezone
            )
        )


@experimental
@whitelist_for_serdes
class RuleCondition(AssetCondition):
    """This class represents the condition that a particular AutoMaterializeRule is satisfied."""

    rule: AutoMaterializeRule

    @property
    def unique_id(self) -> str:
        parts = [self.rule.__class__.__name__, self.description]
        return non_secure_md5_hash_str("".join(parts).encode())

    @property
    def description(self) -> str:
        return self.rule.description

    def evaluate(self, context: "AssetConditionEvaluationContext") -> "AssetConditionResult":
        context.root_context.daemon_context.logger.debug(
            f"Evaluating rule: {self.rule.to_snapshot()}"
        )
        evaluation_result = self.rule.evaluate_for_asset(context)
        context.root_context.daemon_context.logger.debug(
            f"Rule returned {evaluation_result.true_subset.size} partitions "
            f"({evaluation_result.end_timestamp - evaluation_result.start_timestamp:.2f} seconds)"
        )
        return evaluation_result


@experimental
@whitelist_for_serdes
class AndAssetCondition(AssetCondition):
    """This class represents the condition that all of its children evaluate to true."""

    operands: Sequence[AssetCondition]

    @property
    def children(self) -> Sequence[AssetCondition]:
        return self.operands

    @property
    def description(self) -> str:
        return "All of"

    def evaluate(self, context: "AssetConditionEvaluationContext") -> "AssetConditionResult":
        child_results: List[AssetConditionResult] = []
        true_subset = context.candidate_subset
        for child in self.children:
            child_context = context.for_child(condition=child, candidate_subset=true_subset)
            child_result = child.evaluate(child_context)
            child_results.append(child_result)
            true_subset &= child_result.true_subset
        return AssetConditionResult.create_from_children(context, true_subset, child_results)


@experimental
@whitelist_for_serdes
class OrAssetCondition(AssetCondition):
    """This class represents the condition that any of its children evaluate to true."""

    operands: Sequence[AssetCondition]

    @property
    def children(self) -> Sequence[AssetCondition]:
        return self.operands

    @property
    def description(self) -> str:
        return "Any of"

    def evaluate(self, context: "AssetConditionEvaluationContext") -> "AssetConditionResult":
        child_results: List[AssetConditionResult] = []
        true_subset = context.empty_subset()
        for child in self.children:
            child_context = context.for_child(
                condition=child, candidate_subset=context.candidate_subset
            )
            child_result = child.evaluate(child_context)
            child_results.append(child_result)
            true_subset |= child_result.true_subset
        return AssetConditionResult.create_from_children(context, true_subset, child_results)


@experimental
@whitelist_for_serdes
class NotAssetCondition(AssetCondition):
    """This class represents the condition that none of its children evaluate to true."""

    operand: AssetCondition

    @property
    def description(self) -> str:
        return "Not"

    @property
    def children(self) -> Sequence[AssetCondition]:
        return [self.operand]

    def evaluate(self, context: "AssetConditionEvaluationContext") -> "AssetConditionResult":
        child_context = context.for_child(
            condition=self.operand, candidate_subset=context.candidate_subset
        )
        child_result = self.operand.evaluate(child_context)
        true_subset = context.candidate_subset - child_result.true_subset

        return AssetConditionResult.create_from_children(context, true_subset, [child_result])


@dataclass(frozen=True)
class AssetConditionResult:
    condition: AssetCondition
    start_timestamp: float
    end_timestamp: float

    true_subset: AssetSubset
    candidate_subset: AssetSubset
    subsets_with_metadata: Sequence[AssetSubsetWithMetadata]

    extra_state: PackableValue
    child_results: Sequence["AssetConditionResult"]

    @staticmethod
    def create_from_children(
        context: "AssetConditionEvaluationContext",
        true_subset: AssetSubset,
        child_results: Sequence["AssetConditionResult"],
    ) -> "AssetConditionResult":
        """Returns a new AssetConditionEvaluation from the given child results."""
        return AssetConditionResult(
            condition=context.condition,
            start_timestamp=context.start_timestamp,
            end_timestamp=pendulum.now("UTC").timestamp(),
            true_subset=true_subset,
            candidate_subset=context.candidate_subset,
            subsets_with_metadata=[],
            child_results=child_results,
            extra_state=None,
        )

    @staticmethod
    def create(
        context: "AssetConditionEvaluationContext",
        true_subset: AssetSubset,
        subsets_with_metadata: Sequence[AssetSubsetWithMetadata] = [],
        extra_state: PackableValue = None,
    ) -> "AssetConditionResult":
        """Returns a new AssetConditionEvaluation from the given parameters."""
        return AssetConditionResult(
            condition=context.condition,
            start_timestamp=context.start_timestamp,
            end_timestamp=pendulum.now("UTC").timestamp(),
            true_subset=true_subset,
            candidate_subset=context.candidate_subset,
            subsets_with_metadata=subsets_with_metadata,
            child_results=[],
            extra_state=extra_state,
        )
