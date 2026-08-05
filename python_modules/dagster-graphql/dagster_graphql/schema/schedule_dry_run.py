from collections.abc import Mapping
from typing import TYPE_CHECKING, Any

import graphene
from dagster._core.definitions.selector import ScheduleSelector
from dagster._core.workspace.permissions import Permissions

from dagster_graphql.implementation.utils import (
    assert_permission_for_schedule,
    capture_error,
    require_permission_check,
)
from dagster_graphql.schema.errors import (
    GraphenePythonError,
    GrapheneScheduleNotFoundError,
    GrapheneUnauthorizedError,
)
from dagster_graphql.schema.inputs import GrapheneScheduleSelector
from dagster_graphql.schema.instigation import GrapheneDryRunInstigationTick

if TYPE_CHECKING:
    from dagster_graphql.schema.util import ResolveInfo


class GrapheneScheduleDryRunResult(graphene.Union):
    class Meta:
        types = (
            GrapheneDryRunInstigationTick,
            GraphenePythonError,
            GrapheneScheduleNotFoundError,
            GrapheneUnauthorizedError,
        )
        name = "ScheduleDryRunResult"


class GrapheneScheduleDryRunMutation(graphene.Mutation):
    """Enable a schedule to launch runs for a job based on external state change."""

    Output = graphene.NonNull(GrapheneScheduleDryRunResult)

    class Arguments:
        selector_data = graphene.NonNull(GrapheneScheduleSelector)
        timestamp = graphene.Float()

    class Meta:
        name = "ScheduleDryRunMutation"

    @capture_error
    @require_permission_check(Permissions.SCHEDULE_DRY_RUN)
    def mutate(
        self, graphene_info: "ResolveInfo", selector_data: Mapping[str, Any], timestamp: float
    ):
        selector = ScheduleSelector.from_graphql_input(selector_data)
        assert_permission_for_schedule(graphene_info, Permissions.SCHEDULE_DRY_RUN, selector)
        return GrapheneDryRunInstigationTick(selector=selector, timestamp=timestamp)


types = [
    GrapheneScheduleDryRunMutation,
    GrapheneScheduleDryRunResult,
]
