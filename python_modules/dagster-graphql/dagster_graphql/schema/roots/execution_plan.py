import graphene

from dagster_graphql.schema.errors import (
    GrapheneInvalidSubsetError,
    GraphenePipelineNotFoundError,
    GraphenePythonError,
)
from dagster_graphql.schema.execution import GrapheneExecutionPlan
from dagster_graphql.schema.pipelines.config import GrapheneRunConfigValidationInvalid


class GrapheneExecutionPlanOrError(graphene.Union):
    class Meta:
        types = (
            GrapheneExecutionPlan,
            GrapheneRunConfigValidationInvalid,
            GraphenePipelineNotFoundError,
            GrapheneInvalidSubsetError,
            GraphenePythonError,
        )
        name = "ExecutionPlanOrError"
