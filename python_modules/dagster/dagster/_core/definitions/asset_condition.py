import functools
import hashlib
from abc import ABC, abstractmethod
from typing import (
    TYPE_CHECKING,
    AbstractSet,
    FrozenSet,
    List,
    NamedTuple,
    Optional,
    Sequence,
    Tuple,
)

import dagster._check as check
from dagster._core.definitions.asset_daemon_cursor import (
    AssetConditionCursorExtras,
)
from dagster._core.definitions.events import AssetKey
from dagster._core.definitions.metadata import MetadataMapping, MetadataValue
from dagster._serdes.serdes import whitelist_for_serdes

from .asset_condition_evaluation_context import (
    AssetConditionEvaluationContext,
)
from .asset_subset import AssetSubset

if TYPE_CHECKING:
    from .auto_materialize_rule import AutoMaterializeRule


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
    """Internal representation of the results of evaluating a node in the evaluation tree."""

    condition_snapshot: AssetConditionSnapshot
    true_subset: AssetSubset
    candidate_subset: Optional[AssetSubset]
    subsets_with_metadata: Sequence[AssetSubsetWithMetadata] = []
    child_evaluations: Sequence["AssetConditionEvaluation"] = []

    @property
    def asset_key(self) -> AssetKey:
        return self.true_subset.asset_key

    def equivalent_to_stored_evaluation(self, other: Optional["AssetConditionEvaluation"]) -> bool:
        """Returns if all fields other than `run_ids` are equal."""
        return (
            other is not None
            and self.condition_snapshot == other.condition_snapshot
            and self.true_subset == other.true_subset
            and self.candidate_subset == other.candidate_subset
            and self.subsets_with_metadata == other.subsets_with_metadata
            and self.child_evaluations == other.child_evaluations
        )

    def discarded_subset(self, condition: "AssetCondition") -> Optional[AssetSubset]:
        not_discard_condition = condition.not_discard_condition
        if not not_discard_condition or len(self.child_evaluations) != 3:
            return None

        not_discard_evaluation = self.child_evaluations[2]
        discard_evaluation = not_discard_evaluation.child_evaluations[0]
        return discard_evaluation.true_subset

    def get_requested_or_discarded_subset(self, condition: "AssetCondition") -> AssetSubset:
        discarded_subset = self.discarded_subset(condition)
        if discarded_subset is None:
            return self.true_subset
        return self.true_subset | discarded_subset

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


class AssetCondition(ABC):
    """An AutomationCondition represents some state of the world that can influence if an asset
    partition should be materialized or not. AutomationConditions can be combined together to create
    new conditions using the `&` (and), `|` (or), and `~` (not) operators.
    """

    @property
    def unique_id(self) -> str:
        parts = [
            self.__class__.__name__,
            *[child.unique_id for child in self.children],
        ]
        return hashlib.md5("".join(parts).encode()).hexdigest()

    @abstractmethod
    def evaluate(
        self, context: AssetConditionEvaluationContext
    ) -> Tuple[AssetConditionEvaluation, Sequence[AssetConditionCursorExtras]]:
        raise NotImplementedError()

    def __and__(self, other: "AssetCondition") -> "AssetCondition":
        # group AndAutomationConditions together
        if isinstance(self, AndAssetCondition):
            return AndAssetCondition(children=[*self.children, other])
        return AndAssetCondition(children=[self, other])

    def __or__(self, other: "AssetCondition") -> "AssetCondition":
        # group OrAutomationConditions together
        if isinstance(self, OrAssetCondition):
            return OrAssetCondition(children=[*self.children, other])
        return OrAssetCondition(children=[self, other])

    def __invert__(self) -> "AssetCondition":
        return NotAssetCondition(children=[self])

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
    def not_discard_condition(self) -> Optional["AssetCondition"]:
        if not self.is_legacy or not len(self.children) == 3:
            return None
        return self.children[-1]

    @functools.cached_property
    def snapshot(self) -> AssetConditionSnapshot:
        """Returns a snapshot of this condition that can be used for serialization."""
        return AssetConditionSnapshot(
            class_name=self.__class__.__name__,
            description=str(self),
            unique_id=self.unique_id,
        )


class RuleCondition(
    NamedTuple("_RuleCondition", [("rule", "AutoMaterializeRule")]),
    AssetCondition,
):
    """This class represents the condition that a particular AutoMaterializeRule is satisfied."""

    @property
    def unique_id(self) -> str:
        parts = [self.rule.__class__.__name__, self.rule.description]
        return hashlib.md5("".join(parts).encode()).hexdigest()

    def evaluate(
        self, context: AssetConditionEvaluationContext
    ) -> Tuple[AssetConditionEvaluation, Sequence[AssetConditionCursorExtras]]:
        context.root_context.daemon_context._verbose_log_fn(  # noqa
            f"Evaluating rule: {self.rule.to_snapshot()}"
        )
        true_subset, subsets_with_metadata = self.rule.evaluate_for_asset(context)
        context.root_context.daemon_context._verbose_log_fn(  # noqa
            f"Rule returned {true_subset.size} partitions"
        )
        return AssetConditionEvaluation(
            condition_snapshot=self.snapshot,
            true_subset=true_subset,
            candidate_subset=context.candidate_subset,
            subsets_with_metadata=subsets_with_metadata,
        ), [AssetConditionCursorExtras(condition_snapshot=self.snapshot, extras={})]


class AndAssetCondition(
    NamedTuple("_AndAssetCondition", [("children", Sequence[AssetCondition])]),
    AssetCondition,
):
    """This class represents the condition that all of its children evaluate to true."""

    def evaluate(
        self, context: AssetConditionEvaluationContext
    ) -> Tuple[AssetConditionEvaluation, Sequence[AssetConditionCursorExtras]]:
        child_evaluations: List[AssetConditionEvaluation] = []
        child_extras: List[AssetConditionCursorExtras] = []
        true_subset = context.candidate_subset
        for child in self.children:
            child_context = context.for_child(condition=child, candidate_subset=true_subset)
            child_evaluation, child_extra = child.evaluate(child_context)
            child_evaluations.append(child_evaluation)
            child_extras.extend(child_extra)
            true_subset &= child_evaluation.true_subset
        return AssetConditionEvaluation(
            condition_snapshot=self.snapshot,
            true_subset=true_subset,
            candidate_subset=context.candidate_subset,
            child_evaluations=child_evaluations,
        ), child_extras


class OrAssetCondition(
    NamedTuple("_OrAssetCondition", [("children", Sequence[AssetCondition])]),
    AssetCondition,
):
    """This class represents the condition that any of its children evaluate to true."""

    def evaluate(
        self, context: AssetConditionEvaluationContext
    ) -> Tuple[AssetConditionEvaluation, Sequence[AssetConditionCursorExtras]]:
        child_evaluations: List[AssetConditionEvaluation] = []
        child_extras: List[AssetConditionCursorExtras] = []
        true_subset = context.empty_subset()
        for child in self.children:
            child_context = context.for_child(
                condition=child, candidate_subset=context.candidate_subset
            )
            child_evaluation, child_extra = child.evaluate(child_context)
            child_evaluations.append(child_evaluation)
            child_extras.extend(child_extra)
            true_subset |= child_evaluation.true_subset
        return AssetConditionEvaluation(
            condition_snapshot=self.snapshot,
            true_subset=true_subset,
            candidate_subset=context.candidate_subset,
            child_evaluations=child_evaluations,
        ), child_extras


class NotAssetCondition(
    NamedTuple("_NotAssetCondition", [("children", Sequence[AssetCondition])]),
    AssetCondition,
):
    """This class represents the condition that none of its children evaluate to true."""

    def __new__(cls, children: Sequence[AssetCondition]):
        check.invariant(len(children) == 1)
        return super().__new__(cls, children)

    @property
    def child(self) -> AssetCondition:
        return self.children[0]

    def evaluate(
        self, context: AssetConditionEvaluationContext
    ) -> Tuple[AssetConditionEvaluation, Sequence[AssetConditionCursorExtras]]:
        child_context = context.for_child(
            condition=self.child, candidate_subset=context.candidate_subset
        )
        child_evaluation, child_extras = self.child.evaluate(child_context)
        true_subset = context.candidate_subset - child_evaluation.true_subset

        return AssetConditionEvaluation(
            condition_snapshot=self.snapshot,
            true_subset=true_subset,
            candidate_subset=context.candidate_subset,
            child_evaluations=[child_evaluation],
        ), child_extras
