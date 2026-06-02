from collections.abc import Mapping
from typing import TYPE_CHECKING, Any

import graphene
from dagster._core.definitions.selector import SensorSelector
from dagster._core.workspace.permissions import Permissions

from dagster_graphql.implementation.utils import (
    assert_permission_for_sensor,
    capture_error,
    require_permission_check,
)
from dagster_graphql.schema.errors import (
    GraphenePythonError,
    GrapheneSensorNotFoundError,
    GrapheneUnauthorizedError,
)
from dagster_graphql.schema.inputs import GrapheneSensorSelector
from dagster_graphql.schema.instigation import GrapheneDryRunInstigationTick

if TYPE_CHECKING:
    from dagster_graphql.schema.util import ResolveInfo


class GrapheneSensorDryRunResult(graphene.Union):
    class Meta:
        types = (
            GraphenePythonError,
            GrapheneSensorNotFoundError,
            GrapheneUnauthorizedError,
            GrapheneDryRunInstigationTick,
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
    @require_permission_check(Permissions.SENSOR_DRY_RUN)
    def mutate(
        self, graphene_info: "ResolveInfo", selector_data: Mapping[str, Any], cursor: str | None
    ):
        selector = SensorSelector.from_graphql_input(selector_data)
        assert_permission_for_sensor(graphene_info, Permissions.SENSOR_DRY_RUN, selector)
        return GrapheneDryRunInstigationTick(selector, timestamp=None, cursor=cursor)
