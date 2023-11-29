from abc import ABC, abstractmethod
from typing import TYPE_CHECKING, AbstractSet, List, NamedTuple, Optional, Sequence, Tuple

from dagster._core.definitions.asset_daemon_cursor import AssetDaemonAssetCursor
from dagster._core.definitions.asset_graph import AssetGraph
from dagster._core.definitions.auto_materialize_rule import AutoMaterializeRule
from dagster._core.definitions.events import AssetKey, AssetKeyPartitionKey

from .asset_automation_condition_cursor import AssetAutomationConditionCursor
from .asset_subset import AssetSubset
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


class AssetAutomationConditionSnapshot(ABC):
    ...


class AssetAutomationConditionCursor:
    ...


class AssetAutomationConditionLeafCursor(AssetAutomationConditionCursor):
    ...


class AssetAutomationConditionEvaluation(NamedTuple):
    result: AssetAutomationConditionResult


class ConditionEvaluation(NamedTuple):
    """Internal representation of the results of evaluating a node in the evaluation tree."""

    condition: "AutomationCondition"
    true_subset: AssetSubset
    results: RuleEvaluationResults = []
    children: Sequence["ConditionEvaluation"] = []
    condition_cursor: Optional[ConditionCursor] = None

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
        to_discard: AssetSubset,
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
            num_requested=(self.true_subset - to_discard).size,
            num_skipped=num_skipped,
            num_discarded=to_discard.size,
            dynamic_partitions_store=instance_queryer,
        )

    def to_asset_cursor(self) -> AssetDaemonAssetCursor:
        ...


class AutomationCondition(ABC):
    @abstractmethod
    def evaluate(self, context: RuleEvaluationContext) -> ConditionEvaluation:
        ...

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
        return InvertAutomationCondition(child=self)


class RuleCondition(
    AutomationCondition, NamedTuple("_RuleCondition", [("rule", AutoMaterializeRule)])
):
    def evaluate(self, context: RuleEvaluationContext) -> ConditionEvaluation:
        context.daemon_context._verbose_log_fn(f"Evaluating rule: {self.rule.to_snapshot()}")  # noqa
        results = self.rule.evaluate_for_asset(context)
        true_subset = context.empty_subset()
        for _, asset_partitions in results:
            true_subset |= AssetSubset.from_asset_partitions_set(
                context.asset_key, context.partitions_def, asset_partitions
            )
        context.daemon_context._verbose_log_fn(f"Rule returned {true_subset.size} partitions")  # noqa
        return ConditionEvaluation(condition=self, true_subset=true_subset, results=results)


class AndAutomationCondition(
    AutomationCondition,
    NamedTuple("_AndAutomationCondition", [("children", Sequence[AutomationCondition])]),
):
    def evaluate(self, context: RuleEvaluationContext) -> ConditionEvaluation:
        child_evaluations: List[ConditionEvaluation] = []
        true_subset = context.candidate_subset
        for child in self.children:
            context = context.with_candidate_subset(true_subset)
            result = child.evaluate(context)
            child_evaluations.append(result)
            true_subset &= result.true_subset
        return ConditionEvaluation(
            condition=self, true_subset=true_subset, children=child_evaluations
        )


class OrAutomationCondition(
    AutomationCondition,
    NamedTuple("_OrAutomationCondition", [("children", Sequence[AutomationCondition])]),
):
    def evaluate(self, context: RuleEvaluationContext) -> ConditionEvaluation:
        child_evaluations: List[ConditionEvaluation] = []
        true_subset = context.empty_subset()
        for child in self.children:
            result = child.evaluate(context)
            child_evaluations.append(result)
            true_subset |= result.true_subset
        return ConditionEvaluation(
            condition=self, true_subset=true_subset, children=child_evaluations
        )


class InvertAutomationCondition(
    AutomationCondition,
    NamedTuple("_InvertAutomationCondition", [("child", AutomationCondition)]),
):
    def evaluate(self, context: RuleEvaluationContext) -> ConditionEvaluation:
        child_evaluation = self.child.evaluate(context)
        return ConditionEvaluation(
            condition=self,
            true_subset=context.candidate_subset - child_evaluation.true_subset,
            children=[child_evaluation],
        )


class AssetAutomationEvaluator(NamedTuple):
    """For now, this is an internal class that is used to help transition from the old format to the
    new. Upstack, the original AutoMaterializePolicy class will be replaced with this.
    """

    condition: AutomationCondition
    max_materializations_per_minute: Optional[int] = 1

    def evaluate(
        self, context: RuleEvaluationContext, from_legacy: bool
    ) -> Tuple[
        AutoMaterializeAssetEvaluation,
        AssetDaemonAssetCursor,
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
        to_discard, discard_results = context.empty_subset(), []
        if self.max_materializations_per_minute is not None:
            discard_context = context.with_candidate_subset(condition_evaluation.true_subset)
            condition = RuleCondition(
                DiscardOnMaxMaterializationsExceededRule(limit=self.max_materializations_per_minute)
            )
            discard_condition_evaluation = condition.evaluate(discard_context)
            to_discard = discard_condition_evaluation.true_subset
            discard_results = discard_condition_evaluation.all_results

        to_materialize = condition_evaluation.true_subset - to_discard

        # hack to get the number of skipped asset partitions
        num_skipped = 0
        if (
            from_legacy
            and isinstance(self.condition, AndAutomationCondition)
            and len(condition_evaluation.children) == 2
        ):
            # the right-hand side of the AndAutomationCondition is the inverse of the set of skip rules
            num_skipped = condition_evaluation.children[1].children[0].true_subset.size

        return (
            condition_evaluation.to_evaluation(
                context.asset_key,
                context.asset_graph,
                context.instance_queryer,
                to_discard,
                discard_results,
                num_skipped=num_skipped,
            ),
            context.cursor.with_updates(
                asset_graph=context.asset_graph,
                newly_materialized_subset=context.newly_materialized_root_subset,
                requested_asset_partitions=to_materialize.asset_partitions,
                discarded_asset_partitions=to_discard.asset_partitions,
            ),
            to_materialize.asset_partitions,
        )
