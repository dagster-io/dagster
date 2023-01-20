from typing import TYPE_CHECKING

from dagster._core.definitions.schedule_definition import ScheduleExecutionData
from dagster._core.definitions.sensor_definition import SensorExecutionData
from dagster._core.host_representation.selector import ScheduleSelector, SensorSelector
from dagster._core.scheduler.instigation import InstigatorTick

from .utils import (
    UserFacingGraphQLError,
)

if TYPE_CHECKING:
    from dagster_graphql.schema.util import HasContext


def evaluate_sensor(graphene_info: "HasContext", selector: SensorSelector, cursor: str) -> SensorExecutionData:
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

def evaluate_schedule(graphene_info: "HasContext", selector: ScheduleSelector) -> ScheduleExecutionData:
    from ..schema.errors import GrapheneScheduleNotFoundError

    location = graphene_info.context.get_repository_location(selector.location_name)
    repository = location.get_repository(selector.repository_name)

    if not repository.has_external_schedule(selector.schedule_name):
        raise UserFacingGraphQLError(GrapheneScheduleNotFoundError(selector.schedule_name))
    instance = graphene_info.context.instance
    external_schedule = repository.get_external_schedule(selector.schedule_name)

    return location.get_external_schedule_execution_data(
        instance=instance,
        repository_handle=repository.handle,
        schedule_name=external_schedule.name,
        scheduled_execution_time=None
    )

def get_next_tick(graphene_info: "HasContext", schedule_selector: ScheduleSelector) -> InstigatorTick:
    location = graphene_info.context.get_repository_location(schedule_selector.location_name)
    repository = location.get_repository(schedule_selector.repository_name)
    external_schedule = repository.get_external_schedule(schedule_selector.schedule_name)
    ticks = graphene_info.context.instance.get_ticks(
        external_schedule.get_external_origin_id(), external_schedule.selector_id, limit=2
    )
    return list(ticks)[-1]