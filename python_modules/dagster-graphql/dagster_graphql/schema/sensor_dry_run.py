from typing import TYPE_CHECKING, Any, Mapping, Optional

import graphene
from dagster._core.definitions.selector import SensorSelector

from dagster_graphql.implementation.utils import capture_error

from .errors import GraphenePythonError, GrapheneSensorNotFoundError
from .inputs import GrapheneSensorSelector
from .instigation import GrapheneDryRunInstigationTick

if TYPE_CHECKING:
    from dagster_graphql.schema.util import ResolveInfo


class GrapheneSensorDryRunResult(graphene.Union):
    class Meta:
        types = (GraphenePythonError, GrapheneSensorNotFoundError, GrapheneDryRunInstigationTick)
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
        return GrapheneDryRunInstigationTick(
            SensorSelector.from_graphql_input(selector_data), timestamp=None, cursor=cursor
        )
