import graphene

from ..errors import GrapheneInvalidSubsetError, GraphenePipelineNotFoundError, GraphenePythonError
from .config import GraphenePipelineConfigValidationValid, GrapheneRunConfigValidationInvalid


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
