import graphene

from ..errors import (
    GraphenePythonError,
    GrapheneGraphNotFoundError,
    GrapheneInvalidSubsetError,
    GraphenePipelineNotFoundError,
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
