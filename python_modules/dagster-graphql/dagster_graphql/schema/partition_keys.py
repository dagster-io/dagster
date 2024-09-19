import graphene

from dagster_graphql.schema.errors import GrapheneError
from dagster_graphql.schema.util import non_null_list


class GraphenePartitionKeys(graphene.ObjectType):
    partitionKeys = non_null_list(graphene.String)

    class Meta:
        name = "PartitionKeys"


class GraphenePartitionSubsetDeserializationError(graphene.ObjectType):
    message = graphene.NonNull(graphene.String)

    class Meta:
        interfaces = (GrapheneError,)
        name = "PartitionSubsetDeserializationError"


class GraphenePartitionKeysOrError(graphene.Union):
    class Meta:
        types = (GraphenePartitionKeys, GraphenePartitionSubsetDeserializationError)
        name = "PartitionKeysOrError"
