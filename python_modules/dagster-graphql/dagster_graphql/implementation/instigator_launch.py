from dagster._core.host_representation import SensorSelector
from dagster._core.host_representation.selector import ScheduleSelector

from .utils import (
    UserFacingGraphQLError,
)


def test_instigator(graphene_info, selector, cursor):
    from ..schema.errors import GrapheneSensorNotFoundError

    location = graphene_info.context.get_repository_location(selector.location_name)
    repository = location.get_repository(selector.repository_name)

    if not repository.has_external_sensor(selector.sensor_name):
        raise UserFacingGraphQLError(GrapheneSensorNotFoundError(selector.sensor_name))
    instance = graphene_info.context.instance
    external_sensor = repository.get_external_sensor(selector.sensor_name)

    return location.get_external_sensor_execution_data(
        instance=instance,
        repository_handle=repository.handle,
        name=external_sensor.name,
        cursor=cursor,
    )


def instigator_selector_from_gql_input(gql_data):
    if gql_data["instigatorSelector"]["instigatorType"] == "SENSOR":
        return SensorSelector.from_graphql_input(gql_data["instigatorSelector"]["instigatorType"])
    else:
        return ScheduleSelector.from_graphql_input(gql_data["instigatorSelector"]["instigatorType"])
