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
from dagster._core.definitions.asset_graph import AssetGraph
from dagster._core.definitions.auto_materialize_rule_evaluation import (
    AutoMaterializeAssetEvaluation,
    AutoMaterializeDecisionType,
    AutoMaterializeRuleEvaluation,
    AutoMaterializeRuleEvaluationData,
)
from dagster._core.definitions.events import AssetKey, AssetKeyPartitionKey
from dagster._core.definitions.metadata import MetadataMapping, MetadataValue

from .asset_condition_evaluation_context import (
    AssetConditionEvaluationContext,
)
from .asset_subset import AssetSubset

if TYPE_CHECKING:
    from dagster._utils.caching_instance_queryer import CachingInstanceQueryer

    from .auto_materialize_rule import AutoMaterializeRule


class AssetConditionSnapshot(NamedTuple):
    """A serializable snapshot of a node in the AutomationCondition tree."""

    class_name: str
    description: str
    child_hashes: Sequence[str]

    @property
    def hash(self) -> str:
        """Returns a unique hash for this node in the tree."""
        return hashlib.md5(
            "".join([self.class_name, self.description, *self.child_hashes]).encode("utf-8")
        ).hexdigest()


class AssetSubsetWithMetdata(NamedTuple):
    """An asset subset with metadata that corresponds to it."""

    subset: AssetSubset
    metadata: MetadataMapping

    @property
    def frozen_metadata(self) -> FrozenSet[Tuple[str, MetadataValue]]:
        return frozenset(self.metadata.items())


class AssetConditionEvaluation(NamedTuple):
    """Internal representation of the results of evaluating a node in the evaluation tree."""

    condition_snapshot: AssetConditionSnapshot
    true_subset: AssetSubset
    candidate_subset: AssetSubset
    subsets_with_metadata: Sequence[AssetSubsetWithMetdata] = []
    child_evaluations: Sequence["AssetConditionEvaluation"] = []

    def all_results(
        self, condition: "AssetCondition"
    ) -> Sequence[Tuple[AutoMaterializeRuleEvaluation, AbstractSet[AssetKeyPartitionKey]]]:
        """This method is a placeholder to allow us to convert this into a shape that other parts
        of the system understand.
        """
        if isinstance(condition, RuleCondition):
            if self.subsets_with_metadata:
                results = [
                    (
                        AutoMaterializeRuleEvaluation(
                            rule_snapshot=condition.rule.to_snapshot(),
                            evaluation_data=AutoMaterializeRuleEvaluationData.from_metadata(
                                elt.metadata
                            ),
                        ),
                        elt.subset.asset_partitions,
                    )
                    for elt in self.subsets_with_metadata
                ]
            else:
                # if not provided specific metadata, just use the true subset
                asset_partitions = self.true_subset.asset_partitions
                results = (
                    [
                        (
                            AutoMaterializeRuleEvaluation(
                                rule_snapshot=condition.rule.to_snapshot(), evaluation_data=None
                            ),
                            asset_partitions,
                        )
                    ]
                    if asset_partitions
                    else []
                )
        else:
            results = []
        for i, child in enumerate(self.child_evaluations):
            results = [*results, *child.all_results(condition.children[i])]
        return results

    def skip_subset_size(self, condition: "AssetCondition") -> int:
        # backcompat way to calculate the set of skipped partitions for legacy policies
        if not condition.is_legacy:
            return 0

        not_skip_evaluation = self.child_evaluations[1]
        skip_evaluation = not_skip_evaluation.child_evaluations[0]
        return skip_evaluation.true_subset.size

    def discard_subset(self, condition: "AssetCondition") -> Optional[AssetSubset]:
        not_discard_condition = condition.not_discard_condition
        if not not_discard_condition or len(self.child_evaluations) != 3:
            return None

        not_discard_evaluation = self.child_evaluations[2]
        discard_evaluation = not_discard_evaluation.child_evaluations[0]
        return discard_evaluation.true_subset

    def discard_subset_size(self, condition: "AssetCondition") -> int:
        discard_subset = self.discard_subset(condition)
        return discard_subset.size if discard_subset else 0

    def for_child(self, child_condition: "AssetCondition") -> Optional["AssetConditionEvaluation"]:
        """Returns the evaluation of a given child condition by finding the child evaluation that
        has an identical hash to the given condition.
        """
        child_hash = child_condition.snapshot.hash
        for child_evaluation in self.child_evaluations:
            if child_evaluation.condition_snapshot.hash == child_hash:
                return child_evaluation

        return None

    def to_evaluation(
        self,
        asset_key: AssetKey,
        asset_graph: AssetGraph,
        instance_queryer: "CachingInstanceQueryer",
    ) -> AutoMaterializeAssetEvaluation:
        """This method is a placeholder to allow us to convert this into a shape that other parts
        of the system understand.
        """
        condition = check.not_none(
            asset_graph.get_auto_materialize_policy(asset_key)
        ).to_asset_condition()

        return AutoMaterializeAssetEvaluation.from_rule_evaluation_results(
            asset_key=asset_key,
            asset_graph=asset_graph,
            asset_partitions_by_rule_evaluation=self.all_results(condition),
            num_requested=self.true_subset.size,
            num_skipped=self.skip_subset_size(condition),
            num_discarded=self.discard_subset_size(condition),
            dynamic_partitions_store=instance_queryer,
        )

    @staticmethod
    def from_evaluation_and_rule(
        evaluation: AutoMaterializeAssetEvaluation,
        asset_graph: AssetGraph,
        rule: "AutoMaterializeRule",
    ) -> "AssetConditionEvaluation":
        asset_key = evaluation.asset_key
        partitions_def = asset_graph.get_partitions_def(asset_key)

        true_subset, subsets_with_metadata = evaluation.get_rule_evaluation_results(
            rule.to_snapshot(), asset_graph
        )
        return AssetConditionEvaluation(
            condition_snapshot=RuleCondition(rule=rule).snapshot,
            true_subset=true_subset,
            candidate_subset=AssetSubset.empty(asset_key, partitions_def)
            if rule.decision_type == AutoMaterializeDecisionType.MATERIALIZE
            else evaluation.get_evaluated_subset(asset_graph),
            subsets_with_metadata=subsets_with_metadata,
        )

    @staticmethod
    def from_evaluation(
        condition: "AssetCondition",
        evaluation: Optional[AutoMaterializeAssetEvaluation],
        asset_graph: AssetGraph,
    ) -> Optional["AssetConditionEvaluation"]:
        """This method is a placeholder to allow us to convert the serialized objects the system
        uses into a more-convenient internal representation.
        """
        if not condition.is_legacy or not evaluation:
            return None

        asset_key = evaluation.asset_key
        partitions_def = asset_graph.get_partitions_def(asset_key)
        empty_subset = AssetSubset.empty(asset_key, partitions_def)

        materialize_condition, not_skip_condition = condition.children[:2]
        skip_condition = not_skip_condition.children[0]
        materialize_rules = [
            materialize_condition.rule
            for materialize_condition in materialize_condition.children
            if isinstance(materialize_condition, RuleCondition)
            and materialize_condition.rule.to_snapshot() in (evaluation.rule_snapshots or set())
        ]
        skip_rules = [
            skip_condition.rule
            for skip_condition in skip_condition.children
            if isinstance(skip_condition, RuleCondition)
            and skip_condition.rule.to_snapshot() in (evaluation.rule_snapshots or set())
        ]
        children = [
            AssetConditionEvaluation(
                condition_snapshot=materialize_condition.snapshot,
                true_subset=empty_subset,
                candidate_subset=empty_subset,
                child_evaluations=[
                    AssetConditionEvaluation.from_evaluation_and_rule(evaluation, asset_graph, rule)
                    for rule in materialize_rules
                ],
            ),
            AssetConditionEvaluation(
                condition_snapshot=not_skip_condition.snapshot,
                true_subset=empty_subset,
                candidate_subset=empty_subset,
                child_evaluations=[
                    AssetConditionEvaluation(
                        condition_snapshot=skip_condition.snapshot,
                        true_subset=empty_subset,
                        candidate_subset=empty_subset,
                        child_evaluations=[
                            AssetConditionEvaluation.from_evaluation_and_rule(
                                evaluation, asset_graph, rule
                            )
                            for rule in skip_rules
                        ],
                    )
                ],
            ),
        ]
        if condition.not_discard_condition:
            discard_condition = condition.not_discard_condition.children[0]
            if isinstance(discard_condition, RuleCondition):
                children.append(
                    AssetConditionEvaluation(
                        condition_snapshot=condition.not_discard_condition.snapshot,
                        true_subset=empty_subset,
                        candidate_subset=empty_subset,
                        child_evaluations=[
                            AssetConditionEvaluation.from_evaluation_and_rule(
                                evaluation, asset_graph, discard_condition.rule
                            )
                        ],
                    )
                )

        return AssetConditionEvaluation(
            condition_snapshot=condition.snapshot,
            true_subset=evaluation.get_requested_subset(asset_graph),
            candidate_subset=empty_subset,
            child_evaluations=children,
        )


class AssetCondition(ABC):
    """An AutomationCondition represents some state of the world that can influence if an asset
    partition should be materialized or not. AutomationConditions can be combined together to create
    new conditions using the `&` (and), `|` (or), and `~` (not) operators.
    """

    @abstractmethod
    def evaluate(self, context: AssetConditionEvaluationContext) -> AssetConditionEvaluation:
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
    def indexed_children(self) -> Sequence[Tuple[int, "AssetCondition"]]:
        return list(enumerate(self.children))

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
            child_hashes=[child.snapshot.hash for child in self.children],
        )


class RuleCondition(
    NamedTuple("_RuleCondition", [("rule", "AutoMaterializeRule")]),
    AssetCondition,
):
    """This class represents the condition that a particular AutoMaterializeRule is satisfied."""

    def evaluate(self, context: AssetConditionEvaluationContext) -> AssetConditionEvaluation:
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
        )


class AndAssetCondition(
    NamedTuple("_AndAssetCondition", [("children", Sequence[AssetCondition])]),
    AssetCondition,
):
    """This class represents the condition that all of its children evaluate to true."""

    def evaluate(self, context: AssetConditionEvaluationContext) -> AssetConditionEvaluation:
        child_evaluations: List[AssetConditionEvaluation] = []
        true_subset = context.candidate_subset
        for index, child in self.indexed_children:
            child_context = context.for_child(
                condition=child, candidate_subset=true_subset, child_index=index
            )
            result = child.evaluate(child_context)
            child_evaluations.append(result)
            true_subset &= result.true_subset
        return AssetConditionEvaluation(
            condition_snapshot=self.snapshot,
            true_subset=true_subset,
            candidate_subset=context.candidate_subset,
            child_evaluations=child_evaluations,
        )


class OrAssetCondition(
    NamedTuple("_OrAssetCondition", [("children", Sequence[AssetCondition])]),
    AssetCondition,
):
    """This class represents the condition that any of its children evaluate to true."""

    def evaluate(self, context: AssetConditionEvaluationContext) -> AssetConditionEvaluation:
        child_evaluations: List[AssetConditionEvaluation] = []
        true_subset = context.empty_subset()
        for index, child in self.indexed_children:
            child_context = context.for_child(
                condition=child, candidate_subset=context.candidate_subset, child_index=index
            )
            result = child.evaluate(child_context)
            child_evaluations.append(result)
            true_subset |= result.true_subset
        return AssetConditionEvaluation(
            condition_snapshot=self.snapshot,
            true_subset=true_subset,
            candidate_subset=context.candidate_subset,
            child_evaluations=child_evaluations,
        )


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

    def evaluate(self, context: AssetConditionEvaluationContext) -> AssetConditionEvaluation:
        child_context = context.for_child(
            condition=self.child, candidate_subset=context.candidate_subset, child_index=0
        )
        result = self.child.evaluate(child_context)
        true_subset = context.candidate_subset - result.true_subset

        return AssetConditionEvaluation(
            condition_snapshot=self.snapshot,
            true_subset=true_subset,
            candidate_subset=context.candidate_subset,
            child_evaluations=[result],
        )
