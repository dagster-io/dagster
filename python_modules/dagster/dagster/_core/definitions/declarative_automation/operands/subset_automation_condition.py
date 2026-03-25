import inspect
from abc import abstractmethod

from dagster._core.asset_graph_view.entity_subset import EntitySubset
from dagster._core.asset_graph_view.timing_metadata import TimingMetadata
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

    async def evaluate(  # pyright: ignore[reportIncompatibleMethodOverride]
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


@record
class TimedSubsetAutomationCondition(BuiltinAutomationCondition[T_EntityKey]):
    """Base class for conditions that compute a subset along with timing metadata.

    Subclasses implement compute_subset_with_timing_metadata() which returns both the subset
    and an optional TimingMetadata. The evaluate() method stores timing metadata directly
    on the AutomationResult for use by SinceCondition.
    """

    @property
    def requires_cursor(self) -> bool:
        return False

    @abstractmethod
    def compute_subset_with_timing_metadata(
        self, context: AutomationContext[T_EntityKey]
    ) -> tuple[EntitySubset[T_EntityKey], TimingMetadata[T_EntityKey] | None]: ...

    async def evaluate(  # pyright: ignore[reportIncompatibleMethodOverride]
        self, context: AutomationContext[T_EntityKey]
    ) -> AutomationResult[T_EntityKey]:
        # don't compute anything if there are no candidates
        if context.candidate_subset.is_empty:
            true_subset = context.get_empty_subset()
            return AutomationResult(context, true_subset)

        if inspect.iscoroutinefunction(self.compute_subset_with_timing_metadata):
            true_subset, timing_metadata = await self.compute_subset_with_timing_metadata(context)
        else:
            true_subset, timing_metadata = self.compute_subset_with_timing_metadata(context)

        return AutomationResult(
            context,
            true_subset,
            timing_metadata=timing_metadata,
        )
