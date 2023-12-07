import dataclasses
from abc import ABC, abstractmethod
from typing import TYPE_CHECKING, AbstractSet, List, NamedTuple, Optional, Sequence, Tuple

import dagster._check as check
from dagster._core.definitions.asset_daemon_cursor import AssetDaemonAssetCursor
from dagster._core.definitions.asset_graph import AssetGraph
from dagster._core.definitions.events import AssetKey, AssetKeyPartitionKey

from .asset_automation_condition_context import (
    AssetAutomationConditionEvaluationContext,
    AssetAutomationEvaluationContext,
)
from .asset_subset import AssetSubset
from .auto_materialize_rule_evaluation import (
    AutoMaterializeAssetEvaluation,
    AutoMaterializeDecisionType,
    AutoMaterializeRuleEvaluation,
)

if TYPE_CHECKING:
    from dagster._utils.caching_instance_queryer import CachingInstanceQueryer

    from .auto_materialize_rule import AutoMaterializeRule, RuleEvaluationResults


class ConditionEvaluation(NamedTuple):
    """Internal representation of the results of evaluating a node in the evaluation tree."""

    condition: "AutomationCondition"
    true_subset: AssetSubset
    candidate_subset: AssetSubset

    results: "RuleEvaluationResults" = []
    child_evaluations: Sequence["ConditionEvaluation"] = []

    # backcompat until we remove the discard concept
    discard_subset: Optional[AssetSubset] = None
    discard_results: Sequence[
        Tuple[AutoMaterializeRuleEvaluation, AbstractSet[AssetKeyPartitionKey]]
    ] = []

    @property
    def all_results(
        self,
    ) -> Sequence[Tuple[AutoMaterializeRuleEvaluation, AbstractSet[AssetKeyPartitionKey]]]:
        """This method is a placeholder to allow us to convert this into a shape that other parts
        of the system understand.
        """
        if isinstance(self.condition, RuleCondition):
            results = [
                (
                    AutoMaterializeRuleEvaluation(
                        rule_snapshot=self.condition.rule.to_snapshot(),
                        evaluation_data=evaluation_data,
                    ),
                    subset,
                )
                for evaluation_data, subset in self.results
            ]
        else:
            results = []
        for child in self.child_evaluations:
            results = [*results, *child.all_results]
        return results

    def for_child(self, child_condition: "AutomationCondition") -> Optional["ConditionEvaluation"]:
        """Returns the evaluation of a given child condition."""
        for child_evaluation in self.child_evaluations:
            if child_evaluation.condition == child_condition:
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
        # backcompat way to calculate the set of skipped partitions for legacy policies
        if self.condition.is_legacy and len(self.child_evaluations) == 2:
            # the first child is the materialize condition, the second child is the negation of
            # the skip condition
            _, nor_skip_evaluation = self.child_evaluations
            skip_evaluation = nor_skip_evaluation.child_evaluations[0]
            skipped_subset_size = skip_evaluation.true_subset.size
        else:
            skipped_subset_size = 0

        discard_subset = self.discard_subset or AssetSubset.empty(
            asset_key, asset_graph.get_partitions_def(asset_key)
        )

        return AutoMaterializeAssetEvaluation.from_rule_evaluation_results(
            asset_key=asset_key,
            asset_graph=asset_graph,
            asset_partitions_by_rule_evaluation=[*self.all_results, *self.discard_results],
            num_requested=(self.true_subset - discard_subset).size,
            num_skipped=skipped_subset_size,
            num_discarded=discard_subset.size,
            dynamic_partitions_store=instance_queryer,
        )

    @staticmethod
    def from_evaluation_and_rule(
        evaluation: AutoMaterializeAssetEvaluation,
        asset_graph: AssetGraph,
        rule: "AutoMaterializeRule",
    ) -> "ConditionEvaluation":
        asset_key = evaluation.asset_key
        partitions_def = asset_graph.get_partitions_def(asset_key)
        empty_subset = AssetSubset.empty(asset_key, partitions_def)
        return ConditionEvaluation(
            condition=RuleCondition(rule=rule),
            true_subset=empty_subset,
            candidate_subset=empty_subset
            if rule.decision_type == AutoMaterializeDecisionType.MATERIALIZE
            else evaluation.get_evaluated_subset(asset_graph),
            discard_subset=empty_subset,
            results=evaluation.get_rule_evaluation_results(rule.to_snapshot(), asset_graph),
        )

    @staticmethod
    def from_evaluation(
        condition: "AutomationCondition",
        evaluation: Optional[AutoMaterializeAssetEvaluation],
        asset_graph: AssetGraph,
    ) -> Optional["ConditionEvaluation"]:
        """This method is a placeholder to allow us to convert the serialized objects the system
        uses into a more-convenient internal representation.
        """
        if not condition.is_legacy or not evaluation:
            return None

        asset_key = evaluation.asset_key
        partitions_def = asset_graph.get_partitions_def(asset_key)
        empty_subset = AssetSubset.empty(asset_key, partitions_def)

        materialize_condition, skip_condition = condition.children
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
            ConditionEvaluation(
                condition=materialize_condition,
                true_subset=empty_subset,
                candidate_subset=empty_subset,
                child_evaluations=[
                    ConditionEvaluation.from_evaluation_and_rule(evaluation, asset_graph, rule)
                    for rule in materialize_rules
                ],
            ),
            ConditionEvaluation(
                condition=skip_condition,
                true_subset=empty_subset,
                candidate_subset=empty_subset,
                child_evaluations=[
                    ConditionEvaluation.from_evaluation_and_rule(evaluation, asset_graph, rule)
                    for rule in skip_rules
                ],
            ),
        ]
        return ConditionEvaluation(
            condition=condition,
            true_subset=evaluation.get_requested_subset(asset_graph),
            discard_subset=evaluation.get_discarded_subset(asset_graph),
            candidate_subset=empty_subset,
            child_evaluations=children,
        )


class AutomationCondition(ABC):
    """An AutomationCondition represents some state of the world that can influence if an asset
    partition should be materialized or not. AutomationConditions can be combined together to create
    new conditions using the `&` (and), `|` (or), and `~` (not) operators.
    """

    @property
    def children(self) -> Sequence["AutomationCondition"]:
        return []

    @abstractmethod
    def evaluate(self, context: AssetAutomationConditionEvaluationContext) -> ConditionEvaluation:
        raise NotImplementedError()

    def __and__(self, other: "AutomationCondition") -> "AutomationCondition":
        # group AndAutomationConditions together
        if isinstance(self, AndAutomationCondition):
            return AndAutomationCondition(children=[*self.children, other])
        return AndAutomationCondition(children=[self, other])

    def __or__(self, other: "AutomationCondition") -> "AutomationCondition":
        # group OrAutomationConditions together
        if isinstance(self, OrAutomationCondition):
            return OrAutomationCondition(children=[*self.children, other])
        return OrAutomationCondition(children=[self, other])

    def __invert__(self) -> "AutomationCondition":
        return NotAutomationCondition(children=[self])

    @property
    def is_legacy(self) -> bool:
        """Returns if this condition is in the legacy format. This is used to determine if we can
        do certain types of backwards-compatible operations on it.
        """
        return (
            isinstance(self, AndAutomationCondition)
            and len(self.children) == 2
            and isinstance(self.children[0], OrAutomationCondition)
            and isinstance(self.children[1], NotAutomationCondition)
        )


class RuleCondition(
    NamedTuple("_RuleCondition", [("rule", "AutoMaterializeRule")]),
    AutomationCondition,
):
    """This class represents the condition that a particular AutoMaterializeRule is satisfied."""

    def evaluate(self, context: AssetAutomationConditionEvaluationContext) -> ConditionEvaluation:
        context.asset_context.daemon_context._verbose_log_fn(  # noqa
            f"Evaluating rule: {self.rule.to_snapshot()}"
        )
        results = self.rule.evaluate_for_asset(context)
        true_subset = context.empty_subset()
        for _, asset_partitions in results:
            true_subset |= AssetSubset.from_asset_partitions_set(
                context.asset_key, context.partitions_def, asset_partitions
            )
        context.asset_context.daemon_context._verbose_log_fn(  # noqa
            f"Rule returned {true_subset.size} partitions"
        )
        return ConditionEvaluation(
            condition=self,
            true_subset=true_subset,
            candidate_subset=context.candidate_subset,
            results=results,
        )


class AndAutomationCondition(
    NamedTuple("_AndAutomationCondition", [("children", Sequence[AutomationCondition])]),
    AutomationCondition,
):
    """This class represents the condition that all of its children evaluate to true."""

    def evaluate(self, context: AssetAutomationConditionEvaluationContext) -> ConditionEvaluation:
        child_evaluations: List[ConditionEvaluation] = []
        true_subset = context.candidate_subset
        for child in self.children:
            child_context = context.for_child(condition=child, candidate_subset=true_subset)
            result = child.evaluate(child_context)
            child_evaluations.append(result)
            true_subset &= result.true_subset
        return ConditionEvaluation(
            condition=self,
            true_subset=true_subset,
            candidate_subset=context.candidate_subset,
            child_evaluations=child_evaluations,
        )


class OrAutomationCondition(
    NamedTuple("_OrAutomationCondition", [("children", Sequence[AutomationCondition])]),
    AutomationCondition,
):
    """This class represents the condition that any of its children evaluate to true."""

    def evaluate(self, context: AssetAutomationConditionEvaluationContext) -> ConditionEvaluation:
        child_evaluations: List[ConditionEvaluation] = []
        true_subset = context.empty_subset()
        for child in self.children:
            child_context = context.for_child(
                condition=child, candidate_subset=context.candidate_subset
            )
            result = child.evaluate(child_context)
            child_evaluations.append(result)
            true_subset |= result.true_subset
        return ConditionEvaluation(
            condition=self,
            true_subset=true_subset,
            candidate_subset=context.candidate_subset,
            child_evaluations=child_evaluations,
        )


class NotAutomationCondition(
    NamedTuple("_NotAutomationCondition", [("children", Sequence[AutomationCondition])]),
    AutomationCondition,
):
    """This class represents the condition that none of its children evaluate to true."""

    def __new__(cls, children: Sequence[AutomationCondition]):
        check.invariant(len(children) == 1)
        return super().__new__(cls, children)

    @property
    def child(self) -> AutomationCondition:
        return self.children[0]

    def evaluate(self, context: AssetAutomationConditionEvaluationContext) -> ConditionEvaluation:
        child_context = context.for_child(
            condition=self.child, candidate_subset=context.candidate_subset
        )
        result = self.child.evaluate(child_context)
        true_subset = context.candidate_subset - result.true_subset

        return ConditionEvaluation(
            condition=self,
            true_subset=true_subset,
            candidate_subset=context.candidate_subset,
            child_evaluations=[result],
        )


class AssetAutomationEvaluator(NamedTuple):
    """For now, this is an internal class that is used to help transition from the old format to the
    new. Upstack, the original AutoMaterializePolicy class will be replaced with this.
    """

    condition: AutomationCondition
    max_materializations_per_minute: Optional[int] = 1

    def evaluate(
        self, context: AssetAutomationEvaluationContext
    ) -> Tuple[ConditionEvaluation, AssetDaemonAssetCursor]:
        """Evaluates the auto materialize policy of a given asset.

        Returns:
        - A ConditionEvaluation object representing information about this evaluation. If
        `report_num_skipped` is set to `True`, then this will attempt to calculate the number of
        skipped partitions in a backwards-compatible way. This can only be done for policies that
        are in the format `(a | b | ...) & ~(c | d | ...).
        - A new AssetDaemonAssetCursor that represents the state of the world after this evaluation.
        """
        from .auto_materialize_rule import DiscardOnMaxMaterializationsExceededRule

        condition_context = context.get_root_condition_context()
        condition_evaluation = self.condition.evaluate(condition_context)

        # this is treated separately from other rules, for now
        discard_subset = context.empty_subset()
        discard_results = []
        if self.max_materializations_per_minute is not None:
            discard_context = dataclasses.replace(
                condition_context, candidate_subset=condition_evaluation.true_subset
            )
            discard_rule = DiscardOnMaxMaterializationsExceededRule(
                limit=self.max_materializations_per_minute
            )
            condition = RuleCondition(discard_rule)
            discard_condition_evaluation = condition.evaluate(discard_context)
            discard_subset = discard_condition_evaluation.true_subset
            discard_results = [
                (AutoMaterializeRuleEvaluation(discard_rule.to_snapshot(), evaluation_data), aps)
                for evaluation_data, aps in discard_condition_evaluation.results
            ]

        return (
            condition_evaluation._replace(
                true_subset=condition_evaluation.true_subset - discard_subset,
                discard_subset=discard_subset,
                discard_results=discard_results,
            ),
            context.get_new_asset_cursor(evaluation=condition_evaluation),
        )
