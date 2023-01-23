from typing import TYPE_CHECKING

from dagster._core.definitions.sensor_definition import SensorExecutionData
from dagster._core.host_representation.selector import SensorSelector

from .utils import (
    UserFacingGraphQLError,
)

if TYPE_CHECKING:
    from dagster_graphql.schema.util import HasContext


def evaluate_sensor(
    graphene_info: "HasContext", selector: SensorSelector, cursor: str
) -> SensorExecutionData:
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
        last_completion_time=None,
        last_run_key=None,
    )
