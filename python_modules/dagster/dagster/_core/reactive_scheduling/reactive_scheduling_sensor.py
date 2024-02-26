from datetime import datetime
from typing import NamedTuple, Optional, Union

from dagster import _check as check
from dagster._core.definitions.assets import AssetsDefinition
from dagster._core.definitions.decorators.sensor_decorator import sensor
from dagster._core.definitions.events import AssetKey
from dagster._core.definitions.run_request import SensorResult, SkipReason
from dagster._core.definitions.sensor_definition import (
    SensorDefinition,
    SensorEvaluationContext,
)
from dagster._serdes.serdes import deserialize_value, serialize_value, whitelist_for_serdes
from dagster._utils.caching_instance_queryer import CachingInstanceQueryer

from .reactive_scheduling_plan import pulse_policy_on_asset


@whitelist_for_serdes
class ReactiveSchedulingCursor(NamedTuple):
    tick_timestamp: float
    user_defined_cursor: Optional[str] = None

    @property
    def tick_dt(self) -> datetime:
        return datetime.fromtimestamp(self.tick_timestamp)

    def to_json(self) -> str:
        return serialize_value(self)


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

        previous_cursor: Optional[ReactiveSchedulingCursor] = (
            deserialize_value(context.cursor, as_type=ReactiveSchedulingCursor)
            if context.cursor
            else None
        )

        tick_dt = datetime.now()

        queryer = CachingInstanceQueryer(context.instance, context.repository_def.asset_graph)

        pulse_result = pulse_policy_on_asset(
            asset_key=asset_key,
            repository_def=context.repository_def,
            queryer=queryer,
            tick_dt=tick_dt,
            previous_tick_dt=previous_cursor.tick_dt if previous_cursor else None,
            previous_cursor=previous_cursor.user_defined_cursor if previous_cursor else None,
        )

        return SensorResult(
            run_requests=pulse_result.run_requests,
            cursor=serialize_value(ReactiveSchedulingCursor(tick_timestamp=tick_dt.timestamp())),
        )

    return sensor_fn
