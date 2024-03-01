from dagster import Definitions, asset
from dagster._core.definitions.partition import StaticPartitionsDefinition
from dagster._core.reactive_scheduling.asset_graph_view import AssetSlice
from dagster._core.reactive_scheduling.scheduling_policy import (
    EvaluationResult,
    SchedulingExecutionContext,
    SchedulingPolicy,
    SchedulingResult,
)
from dagster._core.reactive_scheduling.scheduling_sensor import SensorSpec


class AlwaysLaunchSchedulingPolicy(SchedulingPolicy):
    def __init__(self, sensor_spec: SensorSpec):
        self.sensor_spec = sensor_spec

    def tick(
        self, context: SchedulingExecutionContext, asset_slice: AssetSlice
    ) -> SchedulingResult:
        return SchedulingResult(launch=True)

    def evaluate(
        self, context: SchedulingExecutionContext, current_slice: AssetSlice
    ) -> EvaluationResult:
        return EvaluationResult(asset_slice=current_slice)


@asset(
    partitions_def=StaticPartitionsDefinition(["A"]),
    scheduling_policy=AlwaysLaunchSchedulingPolicy(
        SensorSpec(name="test_sensor", description="test_description")
    ),
)
def launchy_asset_2() -> None:
    pass


defs = Definitions([launchy_asset_2])
