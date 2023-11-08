from abc import ABC, abstractmethod
from typing import TYPE_CHECKING, AbstractSet, List, NamedTuple, Optional, Sequence, Tuple, Union

from dagster._core.definitions.asset_graph import AssetGraph
from dagster._core.definitions.auto_materialize_rule import AutoMaterializeRule
from dagster._core.definitions.events import AssetKey, AssetKeyPartitionKey
from dagster._core.definitions.partition import PartitionsSubset

from .auto_materialize_rule import (
    DiscardOnMaxMaterializationsExceededRule,
    RuleEvaluationContext,
    RuleEvaluationResults,
)
from .auto_materialize_rule_evaluation import (
    AutoMaterializeAssetEvaluation,
    AutoMaterializeRuleEvaluation,
)

if TYPE_CHECKING:
    from dagster._utils.caching_instance_queryer import CachingInstanceQueryer

PartitionsSubsetOrBool = Union[PartitionsSubset, bool]


class EvaluationData(NamedTuple):
    ...


class ConditionEvaluation(NamedTuple):
    """Internal representation of the results of evaluating a node in the evaluation tree."""

    condition: "AutoMaterializeCondition"
    true: AbstractSet[AssetKeyPartitionKey]
    results: RuleEvaluationResults = []
    children: Sequence["ConditionEvaluation"] = []

    @property
    def all_results(
        self
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
        for child in self.children:
            results = [*results, *child.all_results]
        return results

    def to_evaluation(
        self,
        asset_key: AssetKey,
        asset_graph: AssetGraph,
        instance_queryer: "CachingInstanceQueryer",
        to_discard: AbstractSet[AssetKeyPartitionKey],
        discard_results: Sequence[
            Tuple[AutoMaterializeRuleEvaluation, AbstractSet[AssetKeyPartitionKey]]
        ],
        num_skipped: int,
    ) -> AutoMaterializeAssetEvaluation:
        """This method is a placeholder to allow us to convert this into a shape that other parts
        of the system understand.
        """
        return AutoMaterializeAssetEvaluation.from_rule_evaluation_results(
            asset_key=asset_key,
            asset_graph=asset_graph,
            asset_partitions_by_rule_evaluation=[*self.all_results, *discard_results],
            num_requested=len(self.true - to_discard),
            num_skipped=num_skipped,
            num_discarded=len(to_discard),
            dynamic_partitions_store=instance_queryer,
        )


class AutoMaterializeCondition(ABC):
    @abstractmethod
    def evaluate(self, context: RuleEvaluationContext) -> ConditionEvaluation:
        ...

    def __and__(self, other: "AutoMaterializeCondition") -> "AutoMaterializeCondition":
        # group AndConditions together
        if isinstance(self, AndCondition):
            return AndCondition(children=[*self.children, other])
        return AndCondition(children=[self, other])

    def __or__(self, other: "AutoMaterializeCondition") -> "AutoMaterializeCondition":
        # group OrConditions together
        if isinstance(self, OrCondition):
            return OrCondition(children=[*self.children, other])
        return OrCondition(children=[self, other])

    def __invert__(self) -> "AutoMaterializeCondition":
        return InvertCondition(child=self)


class RuleCondition(
    AutoMaterializeCondition, NamedTuple("_RuleCondition", [("rule", AutoMaterializeRule)])
):
    def evaluate(self, context: RuleEvaluationContext) -> ConditionEvaluation:
        context.daemon_context._verbose_log_fn(f"Evaluating rule: {self.rule.to_snapshot()}")  # noqa
        results = self.rule.evaluate_for_asset(context)
        true = set()
        for _, asset_partitions in results:
            true |= asset_partitions
        context.daemon_context._verbose_log_fn(f"Rule returned {len(true)} partitions")  # noqa
        return ConditionEvaluation(condition=self, true=true, results=results)


class AndCondition(
    AutoMaterializeCondition,
    NamedTuple("_AndCondition", [("children", Sequence[AutoMaterializeCondition])]),
):
    def evaluate(self, context: RuleEvaluationContext) -> ConditionEvaluation:
        child_evaluations: List[ConditionEvaluation] = []
        subset = context.candidates
        for child in self.children:
            context = context.with_candidates(subset)
            result = child.evaluate(context)
            child_evaluations.append(result)
            subset &= result.true
        return ConditionEvaluation(condition=self, true=subset, children=child_evaluations)


class OrCondition(
    AutoMaterializeCondition,
    NamedTuple("_OrCondition", [("children", Sequence[AutoMaterializeCondition])]),
):
    def evaluate(self, context: RuleEvaluationContext) -> ConditionEvaluation:
        child_evaluations: List[ConditionEvaluation] = []
        subset = set()
        for child in self.children:
            result = child.evaluate(context)
            child_evaluations.append(result)
            subset |= result.true
        return ConditionEvaluation(condition=self, true=subset, children=child_evaluations)


class InvertCondition(
    AutoMaterializeCondition,
    NamedTuple("_InvertCondition", [("child", AutoMaterializeCondition)]),
):
    def evaluate(self, context: RuleEvaluationContext) -> ConditionEvaluation:
        child_evaluation = self.child.evaluate(context)
        return ConditionEvaluation(
            condition=self,
            true=context.candidates - child_evaluation.true,
            children=[child_evaluation],
        )


class AutoMaterializePolicyEvaluator(NamedTuple):
    """For now, this is an internal class that is used to help transition from the old format to the
    new. Upstack, the original AutoMaterializePolicy class will be replaced with this.
    """

    condition: AutoMaterializeCondition
    max_materializations_per_minute: Optional[int] = 1

    def evaluate(
        self, context: RuleEvaluationContext, from_legacy: bool
    ) -> Tuple[
        AutoMaterializeAssetEvaluation,
        AbstractSet[AssetKeyPartitionKey],
        AbstractSet[AssetKeyPartitionKey],
    ]:
        """Evaluates the auto materialize policy of a given asset.

        Returns:
        - An AutoMaterializeAssetEvaluation object representing serializable information about
        this evaluation.
        - The set of AssetKeyPartitionKeys that should be materialized.
        - The set of AssetKeyPartitionKeys that should be discarded.
        """
        condition_evaluation = self.condition.evaluate(context)

        # this is treated separately from other rules, for now
        to_discard, discard_results = set(), []
        if self.max_materializations_per_minute is not None:
            discard_context = context.with_candidates(condition_evaluation.true)
            condition = RuleCondition(
                DiscardOnMaxMaterializationsExceededRule(limit=self.max_materializations_per_minute)
            )
            discard_condition_evaluation = condition.evaluate(discard_context)
            to_discard = discard_condition_evaluation.true
            discard_results = discard_condition_evaluation.all_results

        to_materialize = condition_evaluation.true - to_discard

        # hack to get the number of skipped asset partitions
        num_skipped = 0
        if (
            from_legacy
            and isinstance(self.condition, AndCondition)
            and len(condition_evaluation.children) == 2
        ):
            # the right-hand side of the AndCondition is the inverse of the set of skip rules
            num_skipped = len(condition_evaluation.children[1].children[0].true)

        return (
            condition_evaluation.to_evaluation(
                context.asset_key,
                context.asset_graph,
                context.instance_queryer,
                to_discard,
                discard_results,
                num_skipped=num_skipped,
            ),
            to_materialize,
            to_discard,
        )
