from datetime import datetime
from typing import Union

from dagster import _check as check
from dagster._core.definitions.assets import AssetsDefinition
from dagster._core.definitions.decorators.sensor_decorator import sensor
from dagster._core.definitions.events import AssetKey
from dagster._core.definitions.run_request import SensorResult, SkipReason
from dagster._core.definitions.sensor_definition import (
    SensorDefinition,
    SensorEvaluationContext,
)

from .reactive_scheduling_plan import pulse_policy_on_asset


def build_reactive_scheduling_sensor(
    assets_def: AssetsDefinition, asset_key: AssetKey
) -> SensorDefinition:
    check.invariant(asset_key in assets_def.scheduling_policies_by_key)
    scheduling_policy = assets_def.scheduling_policies_by_key[asset_key]

    assert scheduling_policy.tick_settings

    @sensor(
        name=(
            scheduling_policy.tick_settings.sensor_name
            if scheduling_policy.tick_settings.sensor_name
            else f"{asset_key.to_python_identifier()}_reactive_scheduling_sensor"
        ),
        description=scheduling_policy.tick_settings.description,
        minimum_interval_seconds=10,
        default_status=scheduling_policy.tick_settings.default_status,
        asset_selection="*",
    )
    def sensor_fn(context: SensorEvaluationContext) -> Union[SensorResult, SkipReason]:
        check.invariant(
            context.repository_def, "SensorEvaluationContext must have a repository_def"
        )
        assert context.repository_def

        run_requests = pulse_policy_on_asset(
            asset_key=asset_key,
            repository_def=context.repository_def,
            instance=context.instance,
            # TODO: What is the best way to get time in here?
            evaluation_time=datetime.now(),
        )

        return SensorResult(run_requests=run_requests)

    return sensor_fn
