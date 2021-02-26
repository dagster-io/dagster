import graphene

from ..errors import GraphenePipelineNotFoundError, GraphenePythonError
from ..pipelines.pipeline import GraphenePipeline
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
