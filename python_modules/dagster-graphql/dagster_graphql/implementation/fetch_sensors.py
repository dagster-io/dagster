from dagster import check
from dagster.core.definitions.job import JobType
from dagster.core.host_representation import ExternalSensor, RepositorySelector, SensorSelector
from dagster.core.scheduler.job import JobState, JobStatus
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


def _update_sensor_state(graphene_info, sensor_selector, job_status):
    instance = graphene_info.context.instance
    location = graphene_info.context.get_repository_location(sensor_selector.location_name)
    repository = location.get_repository(sensor_selector.repository_name)
    external_sensor = repository.get_external_job(sensor_selector.sensor_name)

    if not isinstance(external_sensor, ExternalSensor):
        raise UserFacingGraphQLError(
            graphene_info.schema.type_named("SensorNotFoundError")(sensor_selector.sensor_name)
        )

    existing_job_state = instance.get_job_state(external_sensor.get_external_origin_id())
    if not existing_job_state:
        instance.add_job_state(
            JobState(external_sensor.get_external_origin(), JobType.SENSOR, job_status)
        )
    else:
        instance.update_job_state(existing_job_state.with_status(job_status))

    return graphene_info.schema.type_named("Sensor")(graphene_info, external_sensor)


@capture_dauphin_error
def start_sensor(graphene_info, sensor_selector):
    check.inst_param(graphene_info, "graphene_info", ResolveInfo)
    check.inst_param(sensor_selector, "sensor_selector", SensorSelector)

    return _update_sensor_state(graphene_info, sensor_selector, JobStatus.RUNNING)


@capture_dauphin_error
def stop_sensor(graphene_info, sensor_selector):
    check.inst_param(graphene_info, "graphene_info", ResolveInfo)
    check.inst_param(sensor_selector, "sensor_selector", SensorSelector)

    return _update_sensor_state(graphene_info, sensor_selector, JobStatus.STOPPED)
