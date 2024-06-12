import graphene
from dagster._core.remote_representation.external_data import ExternalBlueprintManager

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

    def __init__(self, blueprint_manager: ExternalBlueprintManager):
        self.id = blueprint_manager.name
        self.name = blueprint_manager.name
        self.schema = (
            GrapheneJsonSchema(schema=blueprint_manager.schema.schema)
            if blueprint_manager.schema
            else None
        )


class GrapheneBlueprintManagersList(graphene.ObjectType):
    results = non_null_list(GrapheneBlueprintManager)

    class Meta:
        name = "BlueprintManagersList"


class GrapheneBlueprintManagersListOrError(graphene.Union):
    class Meta:
        types = (GrapheneBlueprintManagersList, GraphenePythonError)
        name = "BlueprintManagersListOrError"


class GrapheneBlueprintManagerOrError(graphene.Union):
    class Meta:
        types = (GrapheneBlueprintManager, GraphenePythonError)
        name = "BlueprintManagerOrError"
