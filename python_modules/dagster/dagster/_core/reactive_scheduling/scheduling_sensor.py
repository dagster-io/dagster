from collections import defaultdict
from datetime import datetime
from typing import AbstractSet, Dict, List, NamedTuple, Optional, Sequence, Set

import pendulum

from dagster import _check as check
from dagster._core.definitions.assets import AssetsDefinition
from dagster._core.definitions.data_version import CachingStaleStatusResolver
from dagster._core.definitions.events import AssetKey
from dagster._core.definitions.run_request import BackfillRequest, SensorResult
from dagster._core.definitions.sensor_definition import (
    DefaultSensorStatus,
    SensorDefinition,
    SensorEvaluationContext,
)
from dagster._core.reactive_scheduling.asset_graph_view import AssetGraphView, TemporalContext
from dagster._core.reactive_scheduling.scheduling_plan import (
    ReactiveSchedulingPlan,
    build_reactive_scheduling_plan,
)
from dagster._core.reactive_scheduling.scheduling_policy import SchedulingExecutionContext
from dagster._serdes.serdes import serialize_value, whitelist_for_serdes


class SensorSpec(NamedTuple):
    # TODO Make this optional and have autonaming scheme
    name: str
    default_status: DefaultSensorStatus = DefaultSensorStatus.STOPPED
    description: Optional[str] = None
    # TODO: Possiblye support tick cron rather than just minimum interval
    # tick_cron: str = "* * * * *"
    minimum_interval_seconds: int = 10


class ReactiveSensorInfo:
    def __init__(
        self,
        assets_defs: Sequence[AssetsDefinition],
        asset_keys: Set[AssetKey],
        sensor_spec: SensorSpec,
    ):
        self.asset_keys = asset_keys
        self.sensor_spec = sensor_spec
        self.assets_defs = assets_defs

    def assets_def_for_key(self, asset_key: AssetKey) -> AssetsDefinition:
        for assets_def in self.assets_defs:
            if asset_key in assets_def.keys:
                return assets_def
        check.failed(f"Could not find assets def for key {asset_key}")


@whitelist_for_serdes
class ReactiveSensorCursor(NamedTuple):
    tick_timestamp: float
    tick_timezone: str
    user_defined_cursor: Optional[str] = None

    @staticmethod
    def from_pendulum_datetime(dt: datetime, user_cursor: Optional[str]) -> "ReactiveSensorCursor":
        return ReactiveSensorCursor(
            tick_timestamp=dt.timestamp(),
            tick_timezone=dt.timezone_name,  # pyright: ignore
            user_defined_cursor=user_cursor,
        )

    @property
    def tick_dt(self) -> datetime:
        return pendulum.from_timestamp(self.tick_timestamp, tz=self.tick_timezone)

    def to_json(self) -> str:
        return serialize_value(self)


def pulse_reactive_scheduling(
    context: SchedulingExecutionContext, asset_keys: AbstractSet[AssetKey]
) -> ReactiveSchedulingPlan:
    starting_slices = []
    for asset_key in asset_keys:
        scheduling_info = context.get_scheduling_info(asset_key)
        assert scheduling_info.scheduling_policy
        result = scheduling_info.scheduling_policy.schedule_launch(
            context,
            asset_slice=context.asset_graph_view.slice_factory.complete_asset_slice(asset_key),
        )

        check.invariant(
            result,
            f"scheduling_info.scheduling_policy {scheduling_info.scheduling_policy} did not return a result",
        )

        if result.launch:
            # TODO: filter to most recent by default?
            starting_slices.append(
                result.explicit_launching_slice
                if result.explicit_launching_slice
                else context.asset_graph_view.slice_factory.complete_asset_slice(asset_key)
            )

    return build_reactive_scheduling_plan(
        context, starting_slices=starting_slices
    )  # TODO actually get slices


def build_scheduling_execution_context(
    context: SensorEvaluationContext, tick_dt: datetime
) -> SchedulingExecutionContext:
    assert context.repository_def
    stale_resolver = CachingStaleStatusResolver(
        context.instance, context.repository_def.asset_graph
    )
    check.invariant(stale_resolver.instance_queryer)  # eagerly construct
    return SchedulingExecutionContext(
        asset_graph_view=AssetGraphView(
            temporal_context=TemporalContext(effective_dt=tick_dt, last_event_id=None),
            stale_resolver=stale_resolver,
        ),
    )


def build_sensor_from_sensor_info(reactive_sensor_info: ReactiveSensorInfo) -> SensorDefinition:
    from dagster._core.definitions.decorators.sensor_decorator import sensor

    @sensor(
        name=reactive_sensor_info.sensor_spec.name,
        minimum_interval_seconds=10,  # TODO respect tick cron schedule?
        default_status=reactive_sensor_info.sensor_spec.default_status,
        description=reactive_sensor_info.sensor_spec.description,
        asset_selection="*",  # for now
    )
    def _a_sensor(context: SensorEvaluationContext) -> SensorResult:
        check.invariant(
            context.repository_def, "SensorEvaluationContext must have a repository_def"
        )
        assert context.repository_def

        tick_dt = pendulum.now("UTC")  # timezone? get from sensor context?

        scheduling_context = build_scheduling_execution_context(context, tick_dt)

        plan = pulse_reactive_scheduling(scheduling_context, reactive_sensor_info.asset_keys)

        backfill_request = BackfillRequest(
            # TODO: I don't think asset graph subset should be our public API
            asset_partitions=plan.launch_partition_space.asset_graph_subset,
            tags={},
        )

        return SensorResult(
            backfill_requests=[backfill_request],
            cursor=serialize_value(
                ReactiveSensorCursor.from_pendulum_datetime(tick_dt, user_cursor=None)
            ),
        )

    return _a_sensor


def build_reactive_sensors(
    assets_defs: Sequence[AssetsDefinition],
) -> List[SensorDefinition]:
    asset_keys_by_sensor_id: Dict[int, Set[AssetKey]] = defaultdict(set)
    sensor_spec_by_id: Dict[int, SensorSpec] = {}
    for assets_def in assets_defs:
        for asset_key in assets_def.keys:
            if asset_key not in assets_def.scheduling_policies_by_key:
                continue
            scheduling_policy = assets_def.scheduling_policies_by_key[asset_key]
            if not scheduling_policy.sensor_spec:
                continue
            asset_keys_by_sensor_id[id(scheduling_policy.sensor_spec)].add(asset_key)
            sensor_spec_by_id[id(scheduling_policy.sensor_spec)] = scheduling_policy.sensor_spec

    sensor_infos = []
    for spec_id, sensor_spec in sensor_spec_by_id.items():
        sensor_infos.append(
            ReactiveSensorInfo(
                assets_defs=assets_defs,
                asset_keys=asset_keys_by_sensor_id[spec_id],
                sensor_spec=sensor_spec,
            )
        )

    sensors = []
    for sensor_info in sensor_infos:
        sensors.append(build_sensor_from_sensor_info(sensor_info))
    return sensors
