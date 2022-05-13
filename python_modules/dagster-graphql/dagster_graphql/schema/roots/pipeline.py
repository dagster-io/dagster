# pylint: disable=missing-graphene-docstring
import graphene

from ..errors import GrapheneGraphNotFoundError, GraphenePipelineNotFoundError, GraphenePythonError
from ..pipelines.pipeline import GrapheneGraph, GraphenePipeline
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


class GrapheneGraphOrError(graphene.Union):
    class Meta:
        types = (
            GrapheneGraph,
            GrapheneGraphNotFoundError,
            GraphenePythonError,
        )
        name = "GraphOrError"
