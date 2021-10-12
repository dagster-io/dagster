import graphene

from ..errors import GrapheneJobNotFoundError, GraphenePipelineNotFoundError, GraphenePythonError
from ..pipelines.pipeline import GrapheneJob, GraphenePipeline
from ..pipelines.pipeline_errors import GrapheneInvalidSubsetError


class GraphenePipelineOrError(graphene.Union):
    class Meta:
        types = (
            GraphenePipeline,
            GraphenePipelineNotFoundError,
            GrapheneInvalidSubsetError,
            GraphenePythonError,
        )
        name = "PipelineOrError"


class GrapheneJobOrError(graphene.Union):
    class Meta:
        types = (
            GrapheneJob,
            GrapheneJobNotFoundError,
            GraphenePythonError,
        )
        name = "JobOrError"
