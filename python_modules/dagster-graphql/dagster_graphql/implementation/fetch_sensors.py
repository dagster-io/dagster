from dagster import check
from dagster.core.definitions.job import JobType
from dagster.core.host_representation import (
    ExternalSensor,
    PipelineSelector,
    RepositorySelector,
    SensorSelector,
)
from dagster.core.scheduler.job import JobStatus
from graphql.execution.base import ResolveInfo

from .utils import UserFacingGraphQLError, capture_dauphin_error


@capture_dauphin_error
def get_sensors_or_error(graphene_info, repository_selector):
    check.inst_param(graphene_info, "graphene_info", ResolveInfo)
    check.inst_param(repository_selector, "repository_selector", RepositorySelector)

    location = graphene_info.context.get_repository_location(repository_selector.location_name)
    repository = location.get_repository(repository_selector.repository_name)

    return graphene_info.schema.type_named("Sensors")(
        results=[
            graphene_info.schema.type_named("Sensor")(graphene_info, sensor)
            for sensor in repository.get_external_sensors()
        ]
    )


@capture_dauphin_error
def get_sensor_or_error(graphene_info, selector):
    check.inst_param(graphene_info, "graphene_info", ResolveInfo)
    check.inst_param(selector, "selector", SensorSelector)
    location = graphene_info.context.get_repository_location(selector.location_name)
    repository = location.get_repository(selector.repository_name)

    external_job = repository.get_external_job(selector.sensor_name)

    if not external_job or not isinstance(external_job, ExternalSensor):
        raise UserFacingGraphQLError(
            graphene_info.schema.type_named("SensorNotFoundError")(selector.sensor_name)
        )

    return graphene_info.schema.type_named("Sensor")(graphene_info, external_job)


@capture_dauphin_error
def start_sensor(graphene_info, sensor_selector):
    check.inst_param(graphene_info, "graphene_info", ResolveInfo)
    check.inst_param(sensor_selector, "sensor_selector", SensorSelector)

    location = graphene_info.context.get_repository_location(sensor_selector.location_name)
    repository = location.get_repository(sensor_selector.repository_name)
    external_sensor = repository.get_external_job(sensor_selector.sensor_name)
    if not isinstance(external_sensor, ExternalSensor):
        raise UserFacingGraphQLError(
            graphene_info.schema.type_named("SensorNotFoundError")(sensor_selector.sensor_name)
        )
    graphene_info.context.instance.start_sensor(external_sensor)
    return graphene_info.schema.type_named("Sensor")(graphene_info, external_sensor)


@capture_dauphin_error
def stop_sensor(graphene_info, job_origin_id):
    check.inst_param(graphene_info, "graphene_info", ResolveInfo)
    check.str_param(job_origin_id, "job_origin_id")
    instance = graphene_info.context.instance
    job_state = instance.get_job_state(job_origin_id)
    if not job_state:
        return graphene_info.schema.type_named("StopSensorMutationResult")(jobState=None)

    instance.stop_sensor(job_origin_id)
    return graphene_info.schema.type_named("StopSensorMutationResult")(
        job_state=job_state.with_status(JobStatus.STOPPED)
    )


@capture_dauphin_error
def get_unloadable_sensor_states_or_error(graphene_info):
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

    return graphene_info.schema.type_named("JobStates")(
        results=[
            graphene_info.schema.type_named("JobState")(job_state=job_state)
            for job_state in unloadable_states
        ]
    )


def get_sensors_for_pipeline(graphene_info, pipeline_selector):
    check.inst_param(graphene_info, "graphene_info", ResolveInfo)
    check.inst_param(pipeline_selector, "pipeline_selector", PipelineSelector)

    location = graphene_info.context.get_repository_location(pipeline_selector.location_name)
    repository = location.get_repository(pipeline_selector.repository_name)
    external_sensors = repository.get_external_sensors()

    return [
        graphene_info.schema.type_named("Sensor")(graphene_info, external_sensor)
        for external_sensor in external_sensors
        if external_sensor.pipeline_name == pipeline_selector.pipeline_name
    ]
