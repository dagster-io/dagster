from typing import TYPE_CHECKING, Any, Mapping, Optional

import dagster._check as check
import graphene
from dagster._core.definitions.selector import SensorSelector
from dagster._core.definitions.sensor_definition import SensorExecutionData

from dagster_graphql.implementation.utils import capture_error

from ..implementation.sensor_dry_run_utils import sensor_dry_run
from .errors import GraphenePythonError, GrapheneSensorNotFoundError
from .inputs import GrapheneSensorSelector
from .instigation import GrapheneRunRequest

if TYPE_CHECKING:
    from dagster_graphql.schema.util import ResolveInfo


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

    def resolve_cursor(self, _graphene_info: "ResolveInfo"):
        return self._execution_data.cursor

    def resolve_runRequests(self, _graphene_info: "ResolveInfo"):
        run_requests = self._execution_data.run_requests or []
        return [GrapheneRunRequest(run_request) for run_request in run_requests]

    def resolve_skipMessage(self, _graphene_info: "ResolveInfo"):
        return self._execution_data.skip_message


class GrapheneSensorDryRunResult(graphene.Union):
    class Meta:
        types = (
            GrapheneSensorExecutionData,
            GraphenePythonError,
            GrapheneSensorNotFoundError,
        )
        name = "SensorDryRunResult"


class GrapheneSensorDryRunMutation(graphene.Mutation):
    """Enable a sensor to launch runs for a job based on external state change."""

    Output = graphene.NonNull(GrapheneSensorDryRunResult)

    class Arguments:
        selector_data = graphene.NonNull(GrapheneSensorSelector)
        cursor = graphene.String()

    class Meta:
        name = "SensorDryRunMutation"

    @capture_error
    def mutate(
        self, graphene_info: "ResolveInfo", selector_data: Mapping[str, Any], cursor: Optional[str]
    ):
        return sensor_dry_run(
            graphene_info, SensorSelector.from_graphql_input(selector_data), cursor
        )


types = [
    GrapheneSensorDryRunMutation,
    GrapheneSensorDryRunResult,
    GrapheneSensorExecutionData,
]
