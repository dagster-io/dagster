from dagster._core.definitions.asset_subset import ValidAssetSubset
from dagster._core.reactive_scheduling.scheduling_policy import (
    EvaluationResult,
    SchedulingExecutionContext,
    SchedulingPolicy,
    SchedulingResult,
)


class AlwaysIncludeSchedulingPolicy(SchedulingPolicy):
    def evaluate(
        self, context: SchedulingExecutionContext, current_subset: ValidAssetSubset
    ) -> EvaluationResult:
        return EvaluationResult(asset_subset=current_subset)


class NeverIncludeSchedulingPolicy(SchedulingPolicy):
    ...


class AlwaysLaunchSchedulingPolicy(SchedulingPolicy):
    def tick(self, context: SchedulingExecutionContext) -> SchedulingResult:
        return SchedulingResult(launch=True)
