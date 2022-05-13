# pylint: disable=missing-graphene-docstring
import graphene

import dagster._check as check

from ..errors import GrapheneError
from .pipeline import GraphenePipeline


class GrapheneInvalidSubsetError(graphene.ObjectType):
    class Meta:
        interfaces = (GrapheneError,)
        name = "InvalidSubsetError"

    pipeline = graphene.Field(graphene.NonNull(GraphenePipeline))

    def __init__(self, message, pipeline):
        super().__init__()
        self.message = check.str_param(message, "message")
        self.pipeline = pipeline


class GrapheneConfigTypeNotFoundError(graphene.ObjectType):
    class Meta:
        interfaces = (GrapheneError,)
        name = "ConfigTypeNotFoundError"

    pipeline = graphene.NonNull(GraphenePipeline)
    config_type_name = graphene.NonNull(graphene.String)
