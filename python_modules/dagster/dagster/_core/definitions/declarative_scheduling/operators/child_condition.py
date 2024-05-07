from collections import defaultdict
from typing import AbstractSet, Sequence, Tuple

from dagster._core.definitions.asset_key import AssetKey
from dagster._core.definitions.declarative_scheduling.operators.boolean_operators import (
    OrAssetCondition,
)

from ..scheduling_condition import SchedulingCondition, SchedulingResult
from ..scheduling_context import SchedulingContext


class ChildConditionWrapperCondition(SchedulingCondition):
    """Wrapper object which holds a reference to a condition which is shared by one or more
    children of the target asset.
    """

    child_keys: AbstractSet[AssetKey]
    operand: SchedulingCondition

    @property
    def description(self) -> str:
        return (
            f"Condition of {', '.join([key.to_user_string() for key in sorted(self.child_keys)])}"
        )

    def evaluate(self, context: SchedulingContext) -> SchedulingResult:
        child_context = context.for_child_condition(
            child_condition=self.operand, child_index=0, candidate_slice=context.candidate_slice
        )
        child_result = self.operand.evaluate(child_context)
        return SchedulingResult.create_from_children(
            context=context, true_slice=child_result.true_slice, child_results=[child_result]
        )


class ChildCondition(SchedulingCondition):
    """Condition which will represent the union of all child conditions."""

    @property
    def description(self) -> str:
        return "Any SchedulingCondition applied to a child"

    def _get_child_keys_with_condition(
        self, context: SchedulingContext
    ) -> Sequence[Tuple[AbstractSet[AssetKey], SchedulingCondition]]:
        condition_by_tree_unique_id = {}
        asset_keys_by_tree_unique_id = defaultdict(set)

        def _find_reference_conditions(key: AssetKey) -> None:
            # helper function which recursively finds all conditions to wrap
            policy = context.asset_graph.get(key).auto_materialize_policy
            condition = policy.to_scheduling_condition() if policy else None
            if condition is None:
                return
            elif isinstance(condition, ChildCondition):
                # do not wrap ChildConditions, just recurse
                for child_key in context.asset_graph.get(key).child_keys:
                    _find_reference_conditions(child_key)
            else:
                # found a non-ChildCondition to wrap
                unique_id = condition.get_tree_unique_id()
                condition_by_tree_unique_id[unique_id] = condition
                asset_keys_by_tree_unique_id[unique_id].add(key)

        _find_reference_conditions(context.asset_key)

        return [
            (keys, condition_by_tree_unique_id[uid])
            for uid, keys in asset_keys_by_tree_unique_id.items()
        ]

    def evaluate(self, context: SchedulingContext) -> SchedulingResult:
        child_conditions = self._get_child_keys_with_condition(context)
        if len(child_conditions) == 0:
            # no children, so empty result
            return SchedulingResult.create(
                context,
                true_slice=context.asset_graph_view.create_empty_slice(context.asset_key),
            )
        elif len(child_conditions) == 1:
            # only need to wrap a single child condition
            child_keys, child_condition = child_conditions[0]
            wrapped_condition = ChildConditionWrapperCondition(
                child_keys=child_keys, operand=child_condition
            )
        else:
            # need to wrap multiple child conditions in an OR
            child_wrappers = sorted(
                (
                    ChildConditionWrapperCondition(child_keys=child_keys, operand=child_condition)
                    for child_keys, child_condition in sorted(child_conditions)
                ),
                key=lambda x: sorted(x.child_keys),
            )
            wrapped_condition = OrAssetCondition(operands=child_wrappers)

        # evaluate the wrapped condition
        wrapped_context = context.for_child_condition(
            child_condition=wrapped_condition,
            child_index=0,
            candidate_slice=context.candidate_slice,
        )
        wrapped_result = wrapped_condition.evaluate(wrapped_context)
        return SchedulingResult.create_from_children(
            context, true_slice=wrapped_result.true_slice, child_results=[wrapped_result]
        )
