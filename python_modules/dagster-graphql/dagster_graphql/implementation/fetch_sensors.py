from dagster import check
from dagster.core.definitions.job import JobType
from dagster.core.definitions.sensor import DEFAULT_SENSOR_DAEMON_INTERVAL
from dagster.core.host_representation import (
    ExternalSensor,
    PipelineSelector,
    RepositorySelector,
    SensorSelector,
)
from dagster.core.scheduler.job import JobStatus
from dagster.seven import get_current_datetime_in_utc, get_timestamp_from_utc_datetime
from graphql.execution.base import ResolveInfo

from .utils import UserFacingGraphQLError, capture_error


@capture_error
def get_sensors_or_error(graphene_info, repository_selector):
    from ..schema.sensors import GrapheneSensor, GrapheneSensors

    check.inst_param(graphene_info, "graphene_info", ResolveInfo)
    check.inst_param(repository_selector, "repository_selector", RepositorySelector)

    location = graphene_info.context.get_repository_location(repository_selector.location_name)
    repository = location.get_repository(repository_selector.repository_name)

    return GrapheneSensors(
        results=[
            GrapheneSensor(graphene_info, sensor) for sensor in repository.get_external_sensors()
        ]
    )


@capture_error
def get_sensor_or_error(graphene_info, selector):
    from ..schema.errors import GrapheneSensorNotFoundError
    from ..schema.sensors import GrapheneSensor

    check.inst_param(graphene_info, "graphene_info", ResolveInfo)
    check.inst_param(selector, "selector", SensorSelector)
    location = graphene_info.context.get_repository_location(selector.location_name)
    repository = location.get_repository(selector.repository_name)

    external_job = repository.get_external_job(selector.sensor_name)

    if not external_job or not isinstance(external_job, ExternalSensor):
        raise UserFacingGraphQLError(GrapheneSensorNotFoundError(selector.sensor_name))

    return GrapheneSensor(graphene_info, external_job)


@capture_error
def start_sensor(graphene_info, sensor_selector):
    from ..schema.errors import GrapheneSensorNotFoundError
    from ..schema.sensors import GrapheneSensor

    check.inst_param(graphene_info, "graphene_info", ResolveInfo)
    check.inst_param(sensor_selector, "sensor_selector", SensorSelector)

    location = graphene_info.context.get_repository_location(sensor_selector.location_name)
    repository = location.get_repository(sensor_selector.repository_name)
    external_sensor = repository.get_external_job(sensor_selector.sensor_name)
    if not isinstance(external_sensor, ExternalSensor):
        raise UserFacingGraphQLError(GrapheneSensorNotFoundError(sensor_selector.sensor_name))
    graphene_info.context.instance.start_sensor(external_sensor)
    return GrapheneSensor(graphene_info, external_sensor)


@capture_error
def stop_sensor(graphene_info, job_origin_id):
    from ..schema.sensors import GrapheneStopSensorMutationResult

    check.inst_param(graphene_info, "graphene_info", ResolveInfo)
    check.str_param(job_origin_id, "job_origin_id")
    instance = graphene_info.context.instance
    job_state = instance.get_job_state(job_origin_id)
    if not job_state:
        return GrapheneStopSensorMutationResult(job_state=None)

    instance.stop_sensor(job_origin_id)
    return GrapheneStopSensorMutationResult(job_state=job_state.with_status(JobStatus.STOPPED))


@capture_error
def get_unloadable_sensor_states_or_error(graphene_info):
    from ..schema.jobs import GrapheneJobState, GrapheneJobStates

    sensor_states = graphene_info.context.instance.all_stored_job_state(job_type=JobType.SENSOR)
    external_sensors = [
        sensor
        for repository_location in graphene_info.context.repository_locations
        for repository in repository_location.get_repositories().values()
        for sensor in repository.get_external_sensors()
    ]

    sensor_origin_ids = {
        external_sensor.get_external_origin_id() for external_sensor in external_sensors
    }

    unloadable_states = [
        sensor_state
        for sensor_state in sensor_states
        if sensor_state.job_origin_id not in sensor_origin_ids
    ]

    return GrapheneJobStates(
        results=[GrapheneJobState(job_state=job_state) for job_state in unloadable_states]
    )


def get_sensors_for_pipeline(graphene_info, pipeline_selector):
    from ..schema.sensors import GrapheneSensor

    check.inst_param(graphene_info, "graphene_info", ResolveInfo)
    check.inst_param(pipeline_selector, "pipeline_selector", PipelineSelector)

    location = graphene_info.context.get_repository_location(pipeline_selector.location_name)
    repository = location.get_repository(pipeline_selector.repository_name)
    external_sensors = repository.get_external_sensors()

    return [
        GrapheneSensor(graphene_info, external_sensor)
        for external_sensor in external_sensors
        if external_sensor.pipeline_name == pipeline_selector.pipeline_name
    ]


def get_sensor_next_tick(graphene_info, sensor_state):
    from ..schema.jobs import GrapheneFutureJobTick

    if sensor_state.status != JobStatus.RUNNING:
        return None

    latest_tick = graphene_info.context.instance.get_latest_job_tick(sensor_state.job_origin_id)
    if not latest_tick:
        return None

    next_timestamp = latest_tick.timestamp + DEFAULT_SENSOR_DAEMON_INTERVAL
    if next_timestamp < get_timestamp_from_utc_datetime(get_current_datetime_in_utc()):
        return None
    return GrapheneFutureJobTick(sensor_state, next_timestamp)
