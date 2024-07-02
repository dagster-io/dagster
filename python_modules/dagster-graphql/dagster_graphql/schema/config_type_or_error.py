import graphene

from .errors import (
    GraphenePythonError,
    GraphenePipelineNotFoundError,
    GrapheneConfigTypeNotFoundError,
)
from .config_types import (
    GrapheneEnumConfigType,
    GrapheneRegularConfigType,
    GrapheneCompositeConfigType,
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
