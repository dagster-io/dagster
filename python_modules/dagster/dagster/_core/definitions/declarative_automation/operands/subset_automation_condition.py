import inspect
from abc import abstractmethod

from dagster._core.asset_graph_view.entity_subset import EntitySubset
from dagster._core.definitions.asset_key import T_EntityKey
from dagster._core.definitions.declarative_automation.automation_condition import (
    AutomationResult,
    BuiltinAutomationCondition,
)
from dagster._core.definitions.declarative_automation.automation_context import AutomationContext
from dagster._record import record


@record
class SubsetAutomationCondition(BuiltinAutomationCondition[T_EntityKey]):
    """Base class for simple conditions which compute a simple subset of the asset graph."""

    @property
    def requires_cursor(self) -> bool:
        return False

    @abstractmethod
    def compute_subset(
        self, context: AutomationContext[T_EntityKey]
    ) -> EntitySubset[T_EntityKey]: ...

    async def evaluate(
        self, context: AutomationContext[T_EntityKey]
    ) -> AutomationResult[T_EntityKey]:
        # don't compute anything if there are no candidates
        if context.candidate_subset.is_empty:
            true_subset = context.get_empty_subset()
        elif inspect.iscoroutinefunction(self.compute_subset):
            true_subset = await self.compute_subset(context)
        else:
            true_subset = self.compute_subset(context)

        return AutomationResult(context, true_subset)
