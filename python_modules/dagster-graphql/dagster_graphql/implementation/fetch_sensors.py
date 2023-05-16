from typing import TYPE_CHECKING, Optional, Sequence, Set

import dagster._check as check
from dagster._core.definitions.run_request import InstigatorType
from dagster._core.definitions.selector import JobSubsetSelector, RepositorySelector, SensorSelector
from dagster._core.scheduler.instigation import (
    InstigatorState,
    InstigatorStatus,
    SensorInstigatorData,
)
from dagster._core.workspace.permissions import Permissions
from dagster._seven import get_current_datetime_in_utc, get_timestamp_from_utc_datetime

from dagster_graphql.schema.util import ResolveInfo

from .loader import RepositoryScopedBatchLoader
from .utils import (
    UserFacingGraphQLError,
    assert_permission,
    assert_permission_for_location,
)

if TYPE_CHECKING:
    from dagster_graphql.schema.instigation import GrapheneDryRunInstigationTick

    from ..schema.sensors import GrapheneSensor, GrapheneSensors, GrapheneStopSensorMutationResult


def get_sensors_or_error(
    graphene_info: ResolveInfo,
    repository_selector: RepositorySelector,
    instigator_statuses: Optional[Set[InstigatorStatus]] = None,
) -> "GrapheneSensors":
    from ..schema.sensors import GrapheneSensor, GrapheneSensors

    check.inst_param(repository_selector, "repository_selector", RepositorySelector)

    location = graphene_info.context.get_code_location(repository_selector.location_name)
    repository = location.get_repository(repository_selector.repository_name)
    batch_loader = RepositoryScopedBatchLoader(graphene_info.context.instance, repository)
    sensors = repository.get_external_sensors()
    sensor_states = graphene_info.context.instance.all_instigator_state(
        repository_origin_id=repository.get_external_origin_id(),
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
            GrapheneSensor(sensor, sensor_states_by_name.get(sensor.name), batch_loader)
            for sensor in filtered
        ]
    )


def get_sensor_or_error(graphene_info: ResolveInfo, selector: SensorSelector) -> "GrapheneSensor":
    from ..schema.errors import GrapheneSensorNotFoundError
    from ..schema.sensors import GrapheneSensor

    check.inst_param(selector, "selector", SensorSelector)
    location = graphene_info.context.get_code_location(selector.location_name)
    repository = location.get_repository(selector.repository_name)

    if not repository.has_external_sensor(selector.sensor_name):
        raise UserFacingGraphQLError(GrapheneSensorNotFoundError(selector.sensor_name))
    external_sensor = repository.get_external_sensor(selector.sensor_name)
    sensor_state = graphene_info.context.instance.get_instigator_state(
        external_sensor.get_external_origin_id(),
        external_sensor.selector_id,
    )

    return GrapheneSensor(external_sensor, sensor_state)


def start_sensor(graphene_info: ResolveInfo, sensor_selector: SensorSelector) -> "GrapheneSensor":
    from ..schema.errors import GrapheneSensorNotFoundError
    from ..schema.sensors import GrapheneSensor

    check.inst_param(sensor_selector, "sensor_selector", SensorSelector)

    location = graphene_info.context.get_code_location(sensor_selector.location_name)
    repository = location.get_repository(sensor_selector.repository_name)
    if not repository.has_external_sensor(sensor_selector.sensor_name):
        raise UserFacingGraphQLError(GrapheneSensorNotFoundError(sensor_selector.sensor_name))
    external_sensor = repository.get_external_sensor(sensor_selector.sensor_name)
    graphene_info.context.instance.start_sensor(external_sensor)
    sensor_state = graphene_info.context.instance.get_instigator_state(
        external_sensor.get_external_origin_id(),
        external_sensor.selector_id,
    )
    return GrapheneSensor(external_sensor, sensor_state)


def stop_sensor(
    graphene_info: ResolveInfo, instigator_origin_id: str, instigator_selector_id: str
) -> "GrapheneStopSensorMutationResult":
    from ..schema.sensors import GrapheneStopSensorMutationResult

    check.str_param(instigator_origin_id, "instigator_origin_id")
    instance = graphene_info.context.instance

    external_sensors = {
        sensor.get_external_origin_id(): sensor
        for code_location in graphene_info.context.code_locations
        for repository in code_location.get_repositories().values()
        for sensor in repository.get_external_sensors()
    }

    external_sensor = external_sensors.get(instigator_origin_id)
    if external_sensor:
        assert_permission_for_location(
            graphene_info,
            Permissions.EDIT_SENSOR,
            external_sensor.selector.location_name,
        )
    else:
        assert_permission(
            graphene_info,
            Permissions.EDIT_SENSOR,
        )

    state = instance.stop_sensor(
        instigator_origin_id,
        instigator_selector_id,
        external_sensor,
    )
    return GrapheneStopSensorMutationResult(state)


def get_sensors_for_pipeline(
    graphene_info: ResolveInfo, pipeline_selector: JobSubsetSelector
) -> Sequence["GrapheneSensor"]:
    from ..schema.sensors import GrapheneSensor

    check.inst_param(pipeline_selector, "pipeline_selector", JobSubsetSelector)

    location = graphene_info.context.get_code_location(pipeline_selector.location_name)
    repository = location.get_repository(pipeline_selector.repository_name)
    external_sensors = repository.get_external_sensors()

    results = []
    for external_sensor in external_sensors:
        if pipeline_selector.job_name not in [
            target.job_name for target in external_sensor.get_external_targets()
        ]:
            continue

        sensor_state = graphene_info.context.instance.get_instigator_state(
            external_sensor.get_external_origin_id(),
            external_sensor.selector_id,
        )
        results.append(GrapheneSensor(external_sensor, sensor_state))

    return results


def get_sensor_next_tick(
    graphene_info: ResolveInfo, sensor_state: InstigatorState
) -> Optional["GrapheneDryRunInstigationTick"]:
    from ..schema.instigation import GrapheneDryRunInstigationTick

    check.inst_param(sensor_state, "sensor_state", InstigatorState)

    repository_origin = sensor_state.origin.external_repository_origin
    if not graphene_info.context.has_code_location(
        repository_origin.code_location_origin.location_name
    ):
        return None

    code_location = graphene_info.context.get_code_location(
        repository_origin.code_location_origin.location_name
    )
    if not code_location.has_repository(repository_origin.repository_name):
        return None

    repository = code_location.get_repository(repository_origin.repository_name)

    if not repository.has_external_sensor(sensor_state.name):
        return None

    external_sensor = repository.get_external_sensor(sensor_state.name)

    if not sensor_state.is_running:
        return None

    ticks = graphene_info.context.instance.get_ticks(
        sensor_state.instigator_origin_id, sensor_state.selector_id, limit=1
    )
    if not ticks:
        return None
    latest_tick = ticks[0]

    next_timestamp = latest_tick.timestamp + external_sensor.min_interval_seconds
    if next_timestamp < get_timestamp_from_utc_datetime(get_current_datetime_in_utc()):
        return None
    return GrapheneDryRunInstigationTick(external_sensor.sensor_selector, next_timestamp)


def set_sensor_cursor(
    graphene_info: ResolveInfo, selector: SensorSelector, cursor: Optional[str]
) -> "GrapheneSensor":
    check.inst_param(selector, "selector", SensorSelector)
    check.opt_str_param(cursor, "cursor")

    from ..schema.errors import GrapheneSensorNotFoundError
    from ..schema.sensors import GrapheneSensor

    location = graphene_info.context.get_code_location(selector.location_name)
    repository = location.get_repository(selector.repository_name)

    if not repository.has_external_sensor(selector.sensor_name):
        raise UserFacingGraphQLError(GrapheneSensorNotFoundError(selector.sensor_name))
    instance = graphene_info.context.instance
    external_sensor = repository.get_external_sensor(selector.sensor_name)
    stored_state = instance.get_instigator_state(
        external_sensor.get_external_origin_id(),
        external_sensor.selector_id,
    )
    sensor_state = external_sensor.get_current_instigator_state(stored_state)
    instigator_data = sensor_state.instigator_data
    if not isinstance(instigator_data, SensorInstigatorData):
        check.failed("Expected SensorInstigatorData")
    updated_state = sensor_state.with_data(
        SensorInstigatorData(
            last_tick_timestamp=instigator_data.last_tick_timestamp,
            last_run_key=instigator_data.last_run_key,
            min_interval=external_sensor.min_interval_seconds,
            cursor=cursor,
        )
    )
    if not stored_state:
        instance.add_instigator_state(updated_state)
    else:
        instance.update_instigator_state(updated_state)

    return GrapheneSensor(external_sensor, updated_state)
