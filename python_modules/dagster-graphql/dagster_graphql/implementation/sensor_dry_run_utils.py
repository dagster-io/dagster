from typing import TYPE_CHECKING, Optional

from dagster._core.definitions.selector import SensorSelector

from .utils import UserFacingGraphQLError, capture_error

if TYPE_CHECKING:
    from dagster_graphql.schema.util import ResolveInfo

    from ..schema.sensor_dry_run import GrapheneSensorExecutionData


@capture_error
def sensor_dry_run(
    graphene_info: "ResolveInfo", selector: SensorSelector, cursor: Optional[str]
) -> "GrapheneSensorExecutionData":
    from ..schema.errors import GrapheneSensorNotFoundError
    from ..schema.sensor_dry_run import GrapheneSensorExecutionData

    """Performs a "dry run" of the sensor such that the user code function is
    evaluated, but no tick is persisted to the database, and the cursor is not updated
    for the sensor.
    """

    location = graphene_info.context.get_repository_location(selector.location_name)
    repository = location.get_repository(selector.repository_name)

    if not repository.has_external_sensor(selector.sensor_name):
        raise UserFacingGraphQLError(GrapheneSensorNotFoundError(selector.sensor_name))
    instance = graphene_info.context.instance
    external_sensor = repository.get_external_sensor(selector.sensor_name)

    return GrapheneSensorExecutionData(
        location.get_external_sensor_execution_data(
            instance=instance,
            repository_handle=repository.handle,
            name=external_sensor.name,
            cursor=cursor,
            last_completion_time=None,
            last_run_key=None,
        )
    )
