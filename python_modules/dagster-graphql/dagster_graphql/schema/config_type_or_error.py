import graphene

from dagster_graphql.schema.config_types import (
    GrapheneCompositeConfigType,
    GrapheneEnumConfigType,
    GrapheneRegularConfigType,
)
from dagster_graphql.schema.errors import (
    GrapheneConfigTypeNotFoundError,
    GraphenePipelineNotFoundError,
    GraphenePythonError,
)


class GrapheneConfigTypeOrError(graphene.Union):
    class Meta:
        types = (
            GrapheneEnumConfigType,
            GrapheneCompositeConfigType,
            GrapheneRegularConfigType,
            GraphenePipelineNotFoundError,
            GrapheneConfigTypeNotFoundError,
            GraphenePythonError,
        )
        name = "ConfigTypeOrError"
