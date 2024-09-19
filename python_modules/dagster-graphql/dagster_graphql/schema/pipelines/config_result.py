import graphene

from dagster_graphql.schema.errors import (
    GrapheneInvalidSubsetError,
    GraphenePipelineNotFoundError,
    GraphenePythonError,
)
from dagster_graphql.schema.pipelines.config import (
    GraphenePipelineConfigValidationValid,
    GrapheneRunConfigValidationInvalid,
)


class GraphenePipelineConfigValidationResult(graphene.Union):
    class Meta:
        types = (
            GrapheneInvalidSubsetError,
            GraphenePipelineConfigValidationValid,
            GrapheneRunConfigValidationInvalid,
            GraphenePipelineNotFoundError,
            GraphenePythonError,
        )
        name = "PipelineConfigValidationResult"
