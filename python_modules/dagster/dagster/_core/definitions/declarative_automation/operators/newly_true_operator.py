from collections.abc import Sequence
from typing import Optional

from dagster_shared.serdes import whitelist_for_serdes

from dagster._core.asset_graph_view.entity_subset import EntitySubset
from dagster._core.asset_graph_view.serializable_entity_subset import SerializableEntitySubset
from dagster._core.definitions.asset_key import EntityKey, T_EntityKey
from dagster._core.definitions.declarative_automation.automation_condition import (
    AutomationCondition,
    AutomationResult,
    BuiltinAutomationCondition,
)
from dagster._core.definitions.declarative_automation.automation_context import AutomationContext
from dagster._record import record


@whitelist_for_serdes
@record
class NewlyTrueCondition(BuiltinAutomationCondition[T_EntityKey]):
    operand: AutomationCondition[T_EntityKey]

    @property
    def name(self) -> str:
        return "NEWLY_TRUE"

    @property
    def children(self) -> Sequence[AutomationCondition[T_EntityKey]]:
        return [self.operand]

    def _get_previous_child_true_subset(
        self, context: AutomationContext[T_EntityKey]
    ) -> Optional[EntitySubset[T_EntityKey]]:
        """Returns the true subset of the child from the previous tick, which is stored in the
        extra state field of the cursor.
        """
        true_subset = context.get_structured_cursor(as_type=SerializableEntitySubset)
        if not true_subset:
            return None
        return context.asset_graph_view.get_subset_from_serializable_subset(true_subset)

    def get_node_unique_id(
        self,
        *,
        parent_unique_id: Optional[str],
        index: Optional[int],
        target_key: Optional[EntityKey],
    ) -> str:
        # newly true conditions should have stable cursoring logic regardless of where they
        # exist in the broader condition tree, as they're always evaluated over the entire
        # subset
        return self._get_stable_unique_id(target_key)

    def get_backcompat_node_unique_ids(
        self,
        *,
        parent_unique_id: Optional[str] = None,
        index: Optional[int] = None,
        target_key: Optional[EntityKey] = None,
    ) -> Sequence[str]:
        return [
            # get the standard globally-aware unique id for backcompat purposes
            super().get_node_unique_id(
                parent_unique_id=parent_unique_id, index=index, target_key=target_key
            )
        ]

    async def evaluate(self, context: AutomationContext) -> AutomationResult:  # pyright: ignore[reportIncompatibleMethodOverride]
        # evaluate child condition
        child_result = await context.for_child_condition(
            self.operand,
            child_indices=[0],
            # must evaluate child condition over the entire subset to avoid missing state transitions
            candidate_subset=context.asset_graph_view.get_full_subset(key=context.key),
        ).evaluate_async()

        # get the set of asset partitions of the child which newly became true
        newly_true_child_subset = child_result.true_subset.compute_difference(
            self._get_previous_child_true_subset(context) or context.get_empty_subset()
        )

        return AutomationResult(
            context=context,
            true_subset=context.candidate_subset.compute_intersection(newly_true_child_subset),
            child_results=[child_result],
            structured_cursor=child_result.true_subset.convert_to_serializable_subset(),
        )
