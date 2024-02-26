from dagster import asset
from dagster._core.definitions.definitions_class import Definitions
from dagster._core.definitions.run_request import SensorResult
from dagster._core.definitions.sensor_definition import SensorDefinition, build_sensor_context
from dagster._core.instance import DagsterInstance
from dagster._core.reactive_scheduling.reactive_scheduling_sensor import (
    build_reactive_scheduling_sensor,
)
from dagster._core.reactive_scheduling.scheduling_policy import (
    SchedulingExecutionContext,
    SchedulingPolicy,
    SchedulingResult,
    TickSettings,
)


def test_build_reactive_scheduling_sensor() -> None:
    class AlwaysLaunchSchedulingPolicy(SchedulingPolicy):
        tick_settings = TickSettings(
            tick_cron="* * * * *",
            sensor_name="my_sensor",
            description="my_description",
        )

        def schedule(self, context: SchedulingExecutionContext) -> SchedulingResult:
            return SchedulingResult(launch=True)

    @asset(scheduling_policy=AlwaysLaunchSchedulingPolicy())
    def launchy_asset() -> None:
        pass

    sensor_def = build_reactive_scheduling_sensor(
        assets_def=launchy_asset, asset_key=launchy_asset.key
    )
    assert isinstance(sensor_def, SensorDefinition)
    assert sensor_def.name == "my_sensor"

    defs = Definitions([launchy_asset])

    sensor_context = build_sensor_context(
        instance=DagsterInstance.ephemeral(),
        repository_def=defs.get_repository_def(),
    )

    sensor_result = sensor_def(context=sensor_context)
    assert isinstance(sensor_result, SensorResult)
    assert sensor_result.run_requests
    assert len(sensor_result.run_requests) == 1
    rr = sensor_result.run_requests[0]
    assert rr.asset_selection
    assert set(rr.asset_selection) == {launchy_asset.key}
