import json

import graphene
from dagster._core.remote_representation.external_data import (
    ExternalBlueprint,
    ExternalBlueprintManager,
)

from dagster_graphql.schema.errors import GraphenePythonError
from dagster_graphql.schema.util import non_null_list


class GrapheneJsonSchema(graphene.ObjectType):
    schema = graphene.NonNull(graphene.String)

    class Meta:
        name = "JsonSchema"


class GrapheneBlob(graphene.ObjectType):
    value = graphene.NonNull(graphene.String)

    class Meta:
        name = "Blob"


class GrapheneBlueprintKey(graphene.ObjectType):
    manager_name = graphene.NonNull(graphene.String)
    identifier_within_manager = graphene.NonNull(graphene.String)

    class Meta:
        name = "BlueprintKey"


class GrapheneBlueprint(graphene.ObjectType):
    id = graphene.NonNull(graphene.String)
    key = graphene.NonNull(GrapheneBlueprintKey)
    blob = graphene.Field(GrapheneBlob)

    class Meta:
        name = "Blueprint"

    def __init__(self, blueprint: ExternalBlueprint):
        self.id = blueprint.key.to_string()
        self.key = GrapheneBlueprintKey(
            manager_name=blueprint.key.manager_name,
            identifier_within_manager=blueprint.key.identifier_within_manager,
        )
        self.blob = GrapheneBlob(value=json.dumps(blueprint.blob.value)) if blueprint.blob else None


class GrapheneBlueprintManager(graphene.ObjectType):
    id = graphene.NonNull(graphene.String)
    name = graphene.NonNull(graphene.String)
    schema = graphene.Field(GrapheneJsonSchema)
    blueprints = non_null_list(GrapheneBlueprint)

    class Meta:
        name = "BlueprintManager"

    def __init__(self, blueprint_manager: ExternalBlueprintManager):
        self.id = blueprint_manager.name
        self.name = blueprint_manager.name
        self.schema = (
            GrapheneJsonSchema(schema=json.dumps(blueprint_manager.schema.schema))
            if blueprint_manager.schema
            else None
        )
        self.blueprints = [
            GrapheneBlueprint(blueprint) for blueprint in blueprint_manager.blueprints
        ]


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
