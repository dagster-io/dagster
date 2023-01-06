import dagster._check as check
import graphene
from dagster._core.definitions.sensor_definition import SensorExecutionData
from dagster._core.workspace.permissions import Permissions

from dagster_graphql.implementation.utils import capture_error, check_permission

from ..implementation.instigator_launch import instigator_selector_from_gql_input, test_instigator
from .instigation import GrapheneInstigationState


class GrapheneSensorExecutionData(graphene.ObjectType):
    # TODO: fill out actual fields
    instigatorId = graphene.Field(graphene.String)

    class Meta:
        name = "GrapheneTestInstigatorResult"

    def __init__(self, execution_data):
        super().__init__()
        self._instigator_state = check.inst_param(
            execution_data, "execution_data", SensorExecutionData
        )

    def resolve_instigatorId(self, _graphene_info):
        return GrapheneInstigationState(instigator_state=self._instigator_state)


class GrapheneScheduleExecutionData(graphene.ObjectType):
    # TODO: fill out actual fields
    instigatorId = graphene.Field(graphene.String)

    class Meta:
        name = "GrapheneTestInstigatorResult"

    def __init__(self, execution_data):
        super().__init__()
        self._instigator_state = check.inst_param(
            execution_data, "execution_data", SensorExecutionData
        )

    def resolve_instigatorId(self, _graphene_info):
        return GrapheneInstigationState(instigator_state=self._instigator_state)


class GrapheneTestInstigatorResult(graphene.Union):
    class Meta:
        types = (GrapheneSensorExecutionData, GrapheneScheduleExecutionData)
        name = "SensorOrError"


class GrapheneInstigatorSelector(graphene.InputObjectType):
    repositoryName = graphene.NonNull(graphene.String)
    repositoryLocationName = graphene.NonNull(graphene.String)
    scheduleName = graphene.NonNull(graphene.String)
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
        return test_instigator(
            graphene_info, instigator_selector_from_gql_input(instigator_selector), cursor
        )
