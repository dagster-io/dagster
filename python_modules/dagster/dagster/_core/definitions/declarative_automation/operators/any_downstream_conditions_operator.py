from collections import defaultdict
from collections.abc import Mapping, Sequence
from typing import AbstractSet  # noqa: UP035

from dagster_shared.serdes import whitelist_for_serdes

from dagster._core.definitions.asset_key import AssetKey
from dagster._core.definitions.declarative_automation.automation_condition import (
    AutomationCondition,
    AutomationResult,
    BuiltinAutomationCondition,
)
from dagster._core.definitions.declarative_automation.automation_context import AutomationContext
from dagster._core.definitions.declarative_automation.operators.boolean_operators import (
    AndAutomationCondition,
    OrAutomationCondition,
)
from dagster._record import record


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

    async def evaluate(self, context: AutomationContext[AssetKey]) -> AutomationResult[AssetKey]:  # ty: ignore[invalid-method-override]
        child_result = await context.for_child_condition(
            child_condition=self.operand,
            child_indices=[0],
            candidate_subset=context.candidate_subset,
        ).evaluate_async()

        return AutomationResult(
            context=context,
            true_subset=child_result.true_subset,
            child_results=[child_result],
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

    def _strip_downstream_condition(
        self, condition: AutomationCondition
    ) -> AutomationCondition | None:
        """Simplifies a given downstream condition by (conceptually) substituting any nested
        ``any_downstream_conditions()`` with FALSE, and then collapsing OR/AND nodes accordingly.

        Mathematically, this results in an identical overall result as if you did did not do this
        substitution, but it's simpler conceptually to just imagine the nested adc() conditions being
        ignored.
        """
        # don't unwrap labeled conditions as we'd lose the label information
        if condition.get_label() is not None:
            return condition
        # if the downstream condition is a bare adc() condition, we know all of its
        # contents are redundant and will be captured by the outer adc()
        elif isinstance(condition, AnyDownstreamConditionsCondition):
            return None
        # if the downstream condition is an OR / AND, we can recursively pull out any nested adc()
        # conditions and collapse them into the outer OR / AND after deduplicating
        elif isinstance(condition, (OrAutomationCondition, AndAutomationCondition)):
            kept_operands: list[AutomationCondition] = []
            changed = False
            for operand in condition.operands:
                simplified = self._strip_downstream_condition(operand)
                if simplified is None:
                    changed = True
                    # for AND conditions, if any operand is None, that indicates the
                    # expression as a whole would evaluate to False, so we should drop
                    # the entire condition
                    if isinstance(condition, AndAutomationCondition):
                        return None
                    else:
                        continue
                if simplified is not operand:
                    changed = True
                kept_operands.append(simplified)
            if not changed:
                return condition
            # nothing other than adc() conditions, so entire condition should be dropped
            elif not kept_operands:
                return None
            # single operand, so unwrap it
            elif len(kept_operands) == 1:
                return kept_operands[0]
            # multiple operands, keep wrapped
            else:
                return type(condition)(operands=kept_operands)

        return condition

    def _get_validated_downstream_conditions(
        self, downstream_conditions: Mapping[AutomationCondition, AbstractSet[AssetKey]]
    ) -> Mapping[AutomationCondition, AbstractSet[AssetKey]]:
        collapsed: dict[AutomationCondition, set[AssetKey]] = defaultdict(set)
        for condition, keys in downstream_conditions.items():
            if condition.has_rule_condition:
                continue
            simplified = self._strip_downstream_condition(condition)
            if simplified is None:
                continue
            collapsed[simplified].update(keys)
        return collapsed

    async def evaluate(self, context: AutomationContext[AssetKey]) -> AutomationResult[AssetKey]:  # ty: ignore[invalid-method-override]
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
            child_result = await context.for_child_condition(
                child_condition=DownstreamConditionWrapperCondition(
                    downstream_keys=list(sorted(asset_keys)),
                    operand=downstream_condition,
                ),
                child_indices=[i],
                candidate_subset=context.candidate_subset,
            ).evaluate_async()

            child_results.append(child_result)
            true_subset = true_subset.compute_union(child_result.true_subset)

        return AutomationResult(
            context=context, true_subset=true_subset, child_results=child_results
        )
