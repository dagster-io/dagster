import dagster._check as check
import graphene
from dagster._core.definitions.schedule_definition import ScheduleExecutionData
from dagster._core.definitions.sensor_definition import SensorExecutionData
from dagster._core.workspace.permissions import Permissions

from dagster_graphql.implementation.utils import capture_error, check_permission

from ..implementation.instigator_launch import instigator_selector_from_gql_input, test_instigator
from ..schema.errors import GraphenePythonError
from .instigation import GrapheneRunRequest


class GrapheneInstigatorExecutionData(graphene.ObjectType):
    cursor = graphene.String()
    run_requests = graphene.List(GrapheneRunRequest)
    skip_message = graphene.String()

    class Meta:
        name = "InstigatorExecutionData"

    def __init__(self, execution_data):
        super().__init__()
        self._execution_data = check.inst_param(
            execution_data, "execution_data", (SensorExecutionData, ScheduleExecutionData)
        )

    def resolve_cursor(self, _graphene_info):
        # Not present for schedules
        if isinstance(self._execution_data, ScheduleExecutionData):
            raise Exception("Attempted to retrieve cursor from schedule execution.")
        return self._execution_data.cursor

    def resolve_runRequests(self, _graphene_info):
        return [
            GrapheneRunRequest(run_request) for run_request in self._execution_data.run_requests
        ]

    def resolve_skipMessage(self, _graphene_info):
        return self._execution_data.skip_message


class GrapheneTestInstigatorResult(graphene.Union):
    class Meta:
        types = (
            GrapheneInstigatorExecutionData,
            GraphenePythonError,
        )
        name = "TestInstigatorResult"


class GrapheneInstigatorSelector(graphene.InputObjectType):
    repositoryName = graphene.NonNull(graphene.String)
    repositoryLocationName = graphene.NonNull(graphene.String)
    name = graphene.NonNull(graphene.String)
    instigatorType = graphene.NonNull(graphene.String)

    class Meta:
        description = """This type represents the fields necessary to identify a schedule/sensor."""
        name = "InstigatorSelector"


class GrapheneTestInstigatorMutation(graphene.Mutation):
    """Enable a sensor to launch runs for a job based on external state change."""

    Output = graphene.NonNull(GrapheneTestInstigatorResult)

    class Arguments:
        instigator_selector = graphene.NonNull(GrapheneInstigatorSelector)
        cursor = graphene.String()

    class Meta:
        name = "TestInstigatorMutation"

    @capture_error
    @check_permission(Permissions.EDIT_SENSOR)
    def mutate(self, graphene_info, instigator_selector, cursor):
        test_instigator_result = test_instigator(
            graphene_info, instigator_selector_from_gql_input(instigator_selector), cursor
        )
        return GrapheneInstigatorExecutionData(test_instigator_result)


types = [
    GrapheneTestInstigatorMutation,
    GrapheneInstigatorSelector,
    GrapheneTestInstigatorResult,
    GrapheneInstigatorExecutionData,
]
