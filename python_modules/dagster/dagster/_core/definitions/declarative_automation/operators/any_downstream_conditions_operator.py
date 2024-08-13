from typing import AbstractSet, Optional, Sequence

from dagster._core.definitions.asset_key import AssetKey
from dagster._record import record
from dagster._serdes.serdes import whitelist_for_serdes

from ..automation_condition import AutomationCondition, AutomationResult
from ..automation_context import AutomationContext


@record
class DownstreamConditionWrapperCondition(AutomationCondition):
    """Wrapper object which evaluates a condition against a dependency and returns a subset
    representing the subset of downstream asset which has at least one parent which evaluated to
    True.
    """

    downstream_keys: Sequence[AssetKey]
    operand: AutomationCondition
    label: Optional[str] = None

    @property
    def description(self) -> str:
        return ",".join(key.to_user_string() for key in self.downstream_keys)

    @property
    def children(self) -> Sequence[AutomationCondition]:
        return [self.operand]

    @property
    def requires_cursor(self) -> bool:
        return False

    def evaluate(self, context: AutomationContext) -> AutomationResult:
        child_result = self.operand.evaluate(
            context.for_child_condition(
                child_condition=self.operand, child_index=0, candidate_slice=context.candidate_slice
            )
        )
        return AutomationResult(
            context=context, true_slice=child_result.true_slice, child_results=[child_result]
        )


@whitelist_for_serdes
@record
class AnyDownstreamConditionsCondition(AutomationCondition):
    label: Optional[str] = None

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
        self, context: AutomationContext
    ) -> AbstractSet[AutomationCondition]:
        """To avoid infinite recursion, we do not expand conditions which are already part of the
        evaluation hierarchy.
        """
        ignored_conditions = {context.condition}
        while context.parent_context is not None:
            context = context.parent_context
            ignored_conditions.add(context.condition)
        return ignored_conditions

    def evaluate(self, context: AutomationContext) -> AutomationResult:
        ignored_conditions = self._get_ignored_conditions(context)
        downstream_conditions = context.asset_graph.get_downstream_automation_conditions(
            asset_key=context.asset_key
        )

        true_slice = context.get_empty_slice()
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
                candidate_slice=context.candidate_slice,
            )
            child_result = child_condition.evaluate(child_context)

            child_results.append(child_result)
            true_slice = true_slice.compute_union(child_result.true_slice)

        return AutomationResult(context=context, true_slice=true_slice, child_results=child_results)
