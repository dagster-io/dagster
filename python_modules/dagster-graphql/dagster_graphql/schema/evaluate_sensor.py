from typing import TYPE_CHECKING, Any, Mapping

import dagster._check as check
import graphene
from dagster._core.definitions.schedule_definition import ScheduleExecutionData
from dagster._core.definitions.sensor_definition import SensorExecutionData
from dagster._core.host_representation.selector import SensorSelector
from dagster._core.workspace.permissions import Permissions

from dagster_graphql.implementation.utils import capture_error, check_permission

from ..implementation.evaluate_sensor_utils import evaluate_sensor
from .errors import GraphenePythonError
from .inputs import GrapheneSensorSelector
from .instigation import GrapheneRunRequest

if TYPE_CHECKING:
    from dagster_graphql.schema.util import HasContext


class GrapheneSensorExecutionData(graphene.ObjectType):
    cursor = graphene.String()
    run_requests = graphene.List(GrapheneRunRequest)
    skip_message = graphene.String()

    class Meta:
        name = "SensorExecutionData"

    def __init__(self, execution_data: SensorExecutionData):
        super().__init__()
        self._execution_data = check.inst_param(
            execution_data, "execution_data", SensorExecutionData
        )

    def resolve_cursor(self, _graphene_info: "HasContext"):
        # Not present for schedules
        if isinstance(self._execution_data, ScheduleExecutionData):
            raise Exception("Attempted to retrieve cursor from schedule execution.")
        return self._execution_data.cursor

    def resolve_runRequests(self, _graphene_info: "HasContext"):
        run_requests = self._execution_data.run_requests or []
        return [GrapheneRunRequest(run_request) for run_request in run_requests]

    def resolve_skipMessage(self, _graphene_info: "HasContext"):
        return self._execution_data.skip_message


class GrapheneEvaluateSensorResult(graphene.Union):
    class Meta:
        types = (
            GrapheneSensorExecutionData,
            GraphenePythonError,
        )
        name = "EvaluateSensorMutation"


class GrapheneEvaluateSensorMutation(graphene.Mutation):
    """Enable a sensor to launch runs for a job based on external state change."""

    Output = graphene.NonNull(GrapheneEvaluateSensorResult)

    class Arguments:
        selector_data = graphene.NonNull(GrapheneSensorSelector)
        cursor = graphene.String()

    class Meta:
        name = "EvaluateSensorMutation"

    @capture_error
    @check_permission(Permissions.EDIT_SENSOR)
    def mutate(self, graphene_info: "HasContext", selector_data: Mapping[str, Any], cursor: str):
        sensor_execution_data = evaluate_sensor(
            graphene_info, SensorSelector.from_graphql_input(selector_data), cursor
        )
        return GrapheneSensorExecutionData(sensor_execution_data)


types = [
    GrapheneEvaluateSensorMutation,
    GrapheneEvaluateSensorResult,
    GrapheneSensorExecutionData,
]
