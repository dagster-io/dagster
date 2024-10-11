from typing import AbstractSet, Mapping, Sequence

from dagster._core.definitions.asset_key import AssetKey
from dagster._core.definitions.declarative_automation.automation_condition import (
    AutomationCondition,
    AutomationResult,
    BuiltinAutomationCondition,
)
from dagster._core.definitions.declarative_automation.automation_context import AutomationContext
from dagster._record import record
from dagster._serdes.serdes import whitelist_for_serdes


@record
class DownstreamConditionWrapperCondition(BuiltinAutomationCondition[AssetKey]):
    """Wrapper object which evaluates a condition against a dependency and returns a subset
    representing the subset of downstream asset which has at least one parent which evaluated to
    True.
    """

    downstream_keys: Sequence[AssetKey]
    operand: AutomationCondition

    @property
    def name(self) -> str:
        return ", ".join(key.to_user_string() for key in self.downstream_keys)

    @property
    def children(self) -> Sequence[AutomationCondition]:
        return [self.operand]

    @property
    def requires_cursor(self) -> bool:
        return False

    async def evaluate(self, context: AutomationContext[AssetKey]) -> AutomationResult[AssetKey]:
        child_result = await context.for_child_condition(
            child_condition=self.operand,
            child_index=0,
            candidate_subset=context.candidate_subset,
        ).evaluate_async()

        return AutomationResult(
            context=context, true_subset=child_result.true_subset, child_results=[child_result]
        )


@whitelist_for_serdes
@record
class AnyDownstreamConditionsCondition(BuiltinAutomationCondition[AssetKey]):
    @property
    def description(self) -> str:
        return "Any downstream conditions"

    @property
    def name(self) -> str:
        return "ANY_DOWNSTREAM_CONDITIONS"

    @property
    def requires_cursor(self) -> bool:
        return False

    def _get_ignored_conditions(
        self, context: AutomationContext[AssetKey]
    ) -> AbstractSet[AutomationCondition]:
        """To avoid infinite recursion, we do not expand conditions which are already part of the
        evaluation hierarchy.
        """
        ignored_conditions = {context.condition}
        while context.parent_context is not None:
            context = context.parent_context
            ignored_conditions.add(context.condition)
        return ignored_conditions

    def _get_validated_downstream_conditions(
        self, downstream_conditions: Mapping[AutomationCondition, AbstractSet[AssetKey]]
    ) -> Mapping[AutomationCondition, AbstractSet[AssetKey]]:
        return {
            condition: keys
            for condition, keys in downstream_conditions.items()
            if not condition.has_rule_condition
        }

    async def evaluate(self, context: AutomationContext[AssetKey]) -> AutomationResult[AssetKey]:
        ignored_conditions = self._get_ignored_conditions(context)
        downstream_conditions = self._get_validated_downstream_conditions(
            context.asset_graph.get_downstream_automation_conditions(asset_key=context.key)
        )

        true_subset = context.get_empty_subset()
        child_results = []
        for i, (downstream_condition, asset_keys) in enumerate(
            sorted(downstream_conditions.items(), key=lambda x: sorted(x[1]))
        ):
            if downstream_condition in ignored_conditions:
                continue
            child_condition = DownstreamConditionWrapperCondition(
                downstream_keys=list(sorted(asset_keys)), operand=downstream_condition
            )
            child_context = context.for_child_condition(
                child_condition=child_condition,
                child_index=i,
                candidate_subset=context.candidate_subset,
            )
            child_result = await child_condition.evaluate(child_context)

            child_results.append(child_result)
            true_subset = true_subset.compute_union(child_result.true_subset)

        return AutomationResult(
            context=context, true_subset=true_subset, child_results=child_results
        )
