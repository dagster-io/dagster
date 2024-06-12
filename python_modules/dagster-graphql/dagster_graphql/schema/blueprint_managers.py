import graphene

from dagster_graphql.schema.errors import GraphenePythonError
from dagster_graphql.schema.util import non_null_list


class GrapheneJsonSchema(graphene.ObjectType):
    schema = graphene.NonNull(graphene.String)

    class Meta:
        name = "JsonSchema"


class GrapheneBlueprintManager(graphene.ObjectType):
    id = graphene.NonNull(graphene.String)
    name = graphene.NonNull(graphene.String)
    schema = graphene.Field(GrapheneJsonSchema)

    class Meta:
        name = "BlueprintManager"


class GrapheneBlueprintManagersList(graphene.ObjectType):
    results = non_null_list(GrapheneBlueprintManager)

    class Meta:
        name = "BlueprintManagersList"


class GrapheneBlueprintManagersListOrError(graphene.Union):
    class Meta:
        types = (GrapheneBlueprintManagersList, GraphenePythonError)
        name = "BlueprintManagersOrError"
