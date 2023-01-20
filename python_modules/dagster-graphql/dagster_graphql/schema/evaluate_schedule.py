from typing import TYPE_CHECKING, Any, Mapping

import dagster._check as check
import graphene
from dagster._core.definitions.schedule_definition import ScheduleExecutionData
from dagster._core.host_representation.selector import ScheduleSelector
from dagster._core.scheduler.instigation import InstigatorTick
from dagster._core.workspace.permissions import Permissions

from dagster_graphql.implementation.utils import capture_error, check_permission

from ..implementation.evaluate_instigator_utils import (
    evaluate_schedule,
    get_next_tick,
)
from .errors import GraphenePythonError
from .inputs import GrapheneScheduleSelector
from .instigation import GrapheneRunRequest

if TYPE_CHECKING:
    from dagster_graphql.schema.util import HasContext


class GrapheneScheduleEvaluationData(graphene.ObjectType):
    run_requests = graphene.List(GrapheneRunRequest)
    skip_message = graphene.String()
    next_tick = graphene.NonNull(graphene.Float)

    class Meta:
        name = "InstigatorExecutionData"

    def __init__(self, execution_data: ScheduleExecutionData, next_tick: InstigatorTick):
        super().__init__()
        self._execution_data = check.inst_param(
            execution_data, "execution_data", ScheduleExecutionData
        )
        self._next_tick = check.inst_param(
            next_tick, "next_tick", InstigatorTick
        )

    def resolve_runRequests(self, _graphene_info: "HasContext"):
        run_requests = self._execution_data.run_requests or []
        return [
            GrapheneRunRequest(run_request) for run_request in run_requests
        ]

    def resolve_skipMessage(self, _graphene_info: "HasContext"):
        return self._execution_data.skip_message

    def resolve_nextTick(self, _graphene_info: "HasContext"):
        return self._next_tick.tick_data.timestamp


class GrapheneEvaluateScheduleResult(graphene.Union):
    class Meta:
        types = (
            GrapheneScheduleEvaluationData,
            GraphenePythonError,
        )
        name = "TestInstigatorResult"


class GrapheneEvaluateScheduleMutation(graphene.Mutation):
    """Evaluates a single tick of this schedule ephemerally."""

    Output = graphene.NonNull(GrapheneEvaluateScheduleResult)

    class Arguments:
        schedule_selector = graphene.NonNull(GrapheneScheduleSelector)

    class Meta:
        name = "TestInstigatorMutation"

    @capture_error
    @check_permission(Permissions.EDIT_SENSOR)
    def mutate(self, graphene_info: "HasContext", selector_data: Mapping[str, Any]):
        schedule_selector = ScheduleSelector.from_graphql_input(selector_data)
        schedule_evalation_data = evaluate_schedule(
            graphene_info, schedule_selector
        )
        next_tick = get_next_tick(graphene_info, schedule_selector)
        return GrapheneScheduleEvaluationData(schedule_evalation_data, next_tick)


types = [
    GrapheneEvaluateScheduleMutation,
    GrapheneEvaluateScheduleResult,
    GrapheneScheduleEvaluationData,
]
