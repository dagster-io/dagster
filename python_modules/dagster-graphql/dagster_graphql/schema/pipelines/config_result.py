# pylint: disable=missing-graphene-docstring
import graphene

from ..errors import GraphenePipelineNotFoundError, GraphenePythonError
from .config import GraphenePipelineConfigValidationValid, GrapheneRunConfigValidationInvalid
from .pipeline_errors import GrapheneInvalidSubsetError


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
