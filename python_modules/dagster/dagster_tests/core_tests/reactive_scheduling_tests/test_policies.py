from dagster._core.reactive_scheduling.asset_graph_view import AssetSlice
from dagster._core.reactive_scheduling.scheduling_policy import (
    EvaluationResult,
    SchedulingExecutionContext,
    SchedulingPolicy,
    SchedulingResult,
)


class AlwaysIncludeSchedulingPolicy(SchedulingPolicy):
    def evaluate(
        self, context: SchedulingExecutionContext, current_slice: AssetSlice
    ) -> EvaluationResult:
        return EvaluationResult(asset_slice=current_slice)


class NeverIncludeSchedulingPolicy(SchedulingPolicy):
    ...


class AlwaysLaunchSchedulingPolicy(SchedulingPolicy):
    def tick(self, context: SchedulingExecutionContext) -> SchedulingResult:
        return SchedulingResult(launch=True)
