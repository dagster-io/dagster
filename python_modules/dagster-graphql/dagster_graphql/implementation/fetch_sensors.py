import time
from collections.abc import Sequence
from typing import TYPE_CHECKING, Optional

import dagster._check as check
from dagster._core.definitions.run_request import InstigatorType
from dagster._core.definitions.selector import JobSubsetSelector, RepositorySelector, SensorSelector
from dagster._core.scheduler.instigation import (
    InstigatorState,
    InstigatorStatus,
    SensorInstigatorData,
)
from dagster._core.workspace.permissions import Permissions

from dagster_graphql.implementation.loader import RepositoryScopedBatchLoader
from dagster_graphql.implementation.utils import (
    UserFacingGraphQLError,
    assert_permission,
    assert_permission_for_location,
)
from dagster_graphql.schema.util import ResolveInfo

if TYPE_CHECKING:
    from dagster_graphql.schema.instigation import GrapheneDryRunInstigationTick
    from dagster_graphql.schema.sensors import (
        GrapheneSensor,
        GrapheneSensors,
        GrapheneStopSensorMutationResult,
    )


def get_sensors_or_error(
    graphene_info: ResolveInfo,
    repository_selector: RepositorySelector,
    instigator_statuses: Optional[set[InstigatorStatus]] = None,
) -> "GrapheneSensors":
    from dagster_graphql.schema.sensors import GrapheneSensor, GrapheneSensors

    check.inst_param(repository_selector, "repository_selector", RepositorySelector)

    location = graphene_info.context.get_code_location(repository_selector.location_name)
    repository = location.get_repository(repository_selector.repository_name)
    batch_loader = RepositoryScopedBatchLoader(graphene_info.context.instance, repository)
    sensors = repository.get_sensors()
    sensor_states = graphene_info.context.instance.all_instigator_state(
        repository_origin_id=repository.get_remote_origin_id(),
        repository_selector_id=repository_selector.selector_id,
        instigator_type=InstigatorType.SENSOR,
        instigator_statuses=instigator_statuses,
    )

    sensor_states_by_name = {state.name: state for state in sensor_states}
    if instigator_statuses:
        filtered = [
            sensor
            for sensor in sensors
            if sensor.get_current_instigator_state(sensor_states_by_name.get(sensor.name)).status
            in instigator_statuses
        ]
    else:
        filtered = sensors

    return GrapheneSensors(
        results=[
            GrapheneSensor(
                sensor,
                sensor_states_by_name.get(sensor.name),
                batch_loader,
            )
            for sensor in filtered
        ]
    )


def get_sensor_or_error(graphene_info: ResolveInfo, selector: SensorSelector) -> "GrapheneSensor":
    from dagster_graphql.schema.errors import GrapheneSensorNotFoundError
    from dagster_graphql.schema.sensors import GrapheneSensor

    check.inst_param(selector, "selector", SensorSelector)

    sensor = graphene_info.context.get_sensor(selector)
    if not sensor:
        raise UserFacingGraphQLError(GrapheneSensorNotFoundError(selector.sensor_name))

    sensor_state = graphene_info.context.instance.get_instigator_state(
        sensor.get_remote_origin_id(),
        sensor.selector_id,
    )

    return GrapheneSensor(sensor, sensor_state)


def start_sensor(graphene_info: ResolveInfo, sensor_selector: SensorSelector) -> "GrapheneSensor":
    from dagster_graphql.schema.errors import GrapheneSensorNotFoundError
    from dagster_graphql.schema.sensors import GrapheneSensor

    check.inst_param(sensor_selector, "sensor_selector", SensorSelector)

    sensor = graphene_info.context.get_sensor(sensor_selector)
    if not sensor:
        raise UserFacingGraphQLError(GrapheneSensorNotFoundError(sensor_selector.sensor_name))

    sensor_state = graphene_info.context.instance.start_sensor(sensor)
    return GrapheneSensor(sensor, sensor_state)


def stop_sensor(
    graphene_info: ResolveInfo, instigator_origin_id: str, instigator_selector_id: str
) -> "GrapheneStopSensorMutationResult":
    from dagster_graphql.schema.sensors import GrapheneStopSensorMutationResult

    check.str_param(instigator_origin_id, "instigator_origin_id")
    instance = graphene_info.context.instance

    sensors = {
        sensor.get_remote_origin_id(): sensor
        for code_location in graphene_info.context.code_locations
        for repository in code_location.get_repositories().values()
        for sensor in repository.get_sensors()
    }

    sensor = sensors.get(instigator_origin_id)
    if sensor:
        assert_permission_for_location(
            graphene_info,
            Permissions.EDIT_SENSOR,
            sensor.selector.location_name,
        )
    else:
        assert_permission(
            graphene_info,
            Permissions.EDIT_SENSOR,
        )

    state = instance.stop_sensor(
        instigator_origin_id,
        instigator_selector_id,
        sensor,
    )
    return GrapheneStopSensorMutationResult(state)


def reset_sensor(graphene_info: ResolveInfo, sensor_selector: SensorSelector) -> "GrapheneSensor":
    from dagster_graphql.schema.errors import GrapheneSensorNotFoundError
    from dagster_graphql.schema.sensors import GrapheneSensor

    check.inst_param(sensor_selector, "sensor_selector", SensorSelector)
    sensor = graphene_info.context.get_sensor(sensor_selector)
    if not sensor:
        raise UserFacingGraphQLError(GrapheneSensorNotFoundError(sensor_selector.sensor_name))

    sensor_state = graphene_info.context.instance.reset_sensor(sensor)

    return GrapheneSensor(sensor, sensor_state)


def get_sensors_for_job(
    graphene_info: ResolveInfo, selector: JobSubsetSelector
) -> Sequence["GrapheneSensor"]:
    from dagster_graphql.schema.sensors import GrapheneSensor

    check.inst_param(selector, "selector", JobSubsetSelector)

    sensors = graphene_info.context.get_sensors_targeting_job(selector)

    results = []
    for sensor in sensors:
        sensor_state = graphene_info.context.instance.get_instigator_state(
            sensor.get_remote_origin_id(),
            sensor.selector_id,
        )
        results.append(GrapheneSensor(sensor, sensor_state))

    return results


def get_sensor_next_tick(
    graphene_info: ResolveInfo, sensor_state: InstigatorState
) -> Optional["GrapheneDryRunInstigationTick"]:
    from dagster_graphql.schema.instigation import GrapheneDryRunInstigationTick

    check.inst_param(sensor_state, "sensor_state", InstigatorState)
    if not sensor_state.is_running:
        return None

    repository_origin = sensor_state.origin.repository_origin
    selector = SensorSelector(
        location_name=repository_origin.code_location_origin.location_name,
        repository_name=repository_origin.repository_name,
        sensor_name=sensor_state.name,
    )

    sensor = graphene_info.context.get_sensor(selector)
    if not sensor:
        return None

    ticks = graphene_info.context.instance.get_ticks(
        sensor_state.instigator_origin_id, sensor_state.selector_id, limit=1
    )
    if not ticks:
        return None
    latest_tick = ticks[0]

    next_timestamp = latest_tick.timestamp + sensor.min_interval_seconds
    if next_timestamp < time.time():
        return None
    return GrapheneDryRunInstigationTick(sensor.sensor_selector, next_timestamp)


def set_sensor_cursor(
    graphene_info: ResolveInfo, selector: SensorSelector, cursor: Optional[str]
) -> "GrapheneSensor":
    check.inst_param(selector, "selector", SensorSelector)
    check.opt_str_param(cursor, "cursor")

    from dagster_graphql.schema.errors import GrapheneSensorNotFoundError
    from dagster_graphql.schema.sensors import GrapheneSensor

    sensor = graphene_info.context.get_sensor(selector)
    if not sensor:
        raise UserFacingGraphQLError(GrapheneSensorNotFoundError(selector.sensor_name))

    instance = graphene_info.context.instance
    stored_state = instance.get_instigator_state(
        sensor.get_remote_origin_id(),
        sensor.selector_id,
    )
    sensor_state = sensor.get_current_instigator_state(stored_state)
    instigator_data = sensor_state.instigator_data
    if not isinstance(instigator_data, SensorInstigatorData):
        check.failed("Expected SensorInstigatorData")
    updated_state = sensor_state.with_data(
        SensorInstigatorData(
            last_tick_timestamp=instigator_data.last_tick_timestamp,
            last_run_key=instigator_data.last_run_key,
            min_interval=sensor.min_interval_seconds,
            cursor=cursor,
            sensor_type=sensor.sensor_type,
        )
    )
    if not stored_state:
        instance.add_instigator_state(updated_state)
    else:
        instance.update_instigator_state(updated_state)

    return GrapheneSensor(sensor, updated_state)
