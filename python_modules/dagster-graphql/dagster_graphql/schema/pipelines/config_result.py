import graphene

from ..errors import GraphenePipelineNotFoundError, GraphenePythonError
from .config import GraphenePipelineConfigValidationInvalid, GraphenePipelineConfigValidationValid
from .pipeline_errors import GrapheneInvalidSubsetError


class GraphenePipelineConfigValidationResult(graphene.Union):
    class Meta:
        types = (
            GrapheneInvalidSubsetError,
            GraphenePipelineConfigValidationValid,
            GraphenePipelineConfigValidationInvalid,
            GraphenePipelineNotFoundError,
            GraphenePythonError,
        )
        name = "PipelineConfigValidationResult"
