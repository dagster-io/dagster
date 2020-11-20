from dagster import check
from dagster.core.definitions.job import JobType
from dagster.core.host_representation import RepositorySelector, SensorSelector
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

    if not external_job or external_job.job_type != JobType.SENSOR:
        raise UserFacingGraphQLError(
            graphene_info.schema.type_named("SensorNotFoundError")(selector.sensor_name)
        )

    return graphene_info.schema.type_named("Sensor")(graphene_info, external_job)
