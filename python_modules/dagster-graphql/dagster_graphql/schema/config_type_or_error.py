import graphene

from .config_types import (
    GrapheneCompositeConfigType,
    GrapheneEnumConfigType,
    GrapheneRegularConfigType,
)
from .errors import (
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
