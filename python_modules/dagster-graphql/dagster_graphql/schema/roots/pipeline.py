import graphene

from dagster_graphql.schema.errors import (
    GrapheneGraphNotFoundError,
    GrapheneInvalidSubsetError,
    GraphenePipelineNotFoundError,
    GraphenePythonError,
)
from dagster_graphql.schema.pipelines.pipeline import GrapheneGraph, GraphenePipeline


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
