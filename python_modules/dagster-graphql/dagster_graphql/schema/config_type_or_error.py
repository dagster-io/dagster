import graphene

from .config_types import (
    GrapheneCompositeConfigType,
    GrapheneEnumConfigType,
    GrapheneRegularConfigType,
)
from .errors import GraphenePipelineNotFoundError, GraphenePythonError
from .pipelines.pipeline_errors import GrapheneConfigTypeNotFoundError


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
