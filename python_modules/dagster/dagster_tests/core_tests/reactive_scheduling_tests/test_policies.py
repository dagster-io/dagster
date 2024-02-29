from datetime import datetime
from typing import Optional

import pendulum
from dagster._core.definitions.definitions_class import Definitions
from dagster._core.instance import DagsterInstance
from dagster._core.reactive_scheduling.asset_graph_view import (
    AssetSlice,
)
from dagster._core.reactive_scheduling.scheduling_policy import (
    EvaluationResult,
    SchedulingExecutionContext,
    SchedulingPolicy,
    SchedulingResult,
)
from dagster._core.reactive_scheduling.scheduling_sensor import SensorSpec


class AlwaysIncludeSchedulingPolicy(SchedulingPolicy):
    def evaluate(
        self, context: SchedulingExecutionContext, current_slice: AssetSlice
    ) -> EvaluationResult:
        return EvaluationResult(asset_slice=current_slice)


class NeverIncludeSchedulingPolicy(SchedulingPolicy):
    ...


class AlwaysLaunchSchedulingPolicy(SchedulingPolicy):
    def __init__(self, sensor_spec: SensorSpec):
        self.sensor_spec = sensor_spec

    def tick(self, context: SchedulingExecutionContext) -> SchedulingResult:
        return SchedulingResult(launch=True)

    def evaluate(
        self, context: SchedulingExecutionContext, current_slice: AssetSlice
    ) -> EvaluationResult:
        return EvaluationResult(asset_slice=current_slice)


def build_test_context(
    defs: Definitions,
    instance: Optional[DagsterInstance] = None,
    tick_dt: Optional[datetime] = None,
    last_storage_id: Optional[int] = None,
) -> SchedulingExecutionContext:
    return SchedulingExecutionContext.create(
        instance=instance or DagsterInstance.ephemeral(),
        repository_def=defs.get_repository_def(),
        tick_dt=tick_dt or pendulum.now(),
        last_storage_id=last_storage_id,
    )
