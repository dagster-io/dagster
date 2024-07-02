import graphene

from .config import GrapheneRunConfigValidationInvalid, GraphenePipelineConfigValidationValid
from ..errors import GraphenePythonError, GrapheneInvalidSubsetError, GraphenePipelineNotFoundError


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
