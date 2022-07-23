import graphene

from ..errors import (
    GrapheneGraphNotFoundError,
    GrapheneInvalidSubsetError,
    GraphenePipelineNotFoundError,
    GraphenePythonError,
)
from ..pipelines.pipeline import GrapheneGraph, GraphenePipeline


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
