import graphene
from graphene.types.generic import GenericScalar

from dagster_graphql.schema.errors import GraphenePythonError, GrapheneRepositoryLocationNotFound
from dagster_graphql.schema.util import non_null_list


class GrapheneJsonSchema(GenericScalar, graphene.Scalar):
    """A JSON Schema document, returned as a parsed JSON object."""

    class Meta:
        name = "JsonSchema"


class GrapheneComponentTypeInfo(graphene.ObjectType):
    """Metadata for a single Component class registered in a code location."""

    name = graphene.NonNull(graphene.String)
    schema = graphene.Field(
        GrapheneJsonSchema,
        description=(
            "The JSON Schema describing the component's attributes model. May be"
            " null if the component does not declare a model."
        ),
    )
    description = graphene.String()
    owners = graphene.List(graphene.NonNull(graphene.String))
    tags = graphene.List(graphene.NonNull(graphene.String))

    class Meta:
        name = "ComponentTypeInfo"


class GrapheneComponentTypes(graphene.ObjectType):
    locationName = graphene.NonNull(graphene.String)
    componentTypes = non_null_list(GrapheneComponentTypeInfo)

    class Meta:
        name = "ComponentTypes"


class GrapheneComponentTypesOrError(graphene.Union):
    class Meta:
        types = (
            GrapheneComponentTypes,
            GrapheneRepositoryLocationNotFound,
            GraphenePythonError,
        )
        name = "ComponentTypesOrError"


types = [
    GrapheneJsonSchema,
    GrapheneComponentTypeInfo,
    GrapheneComponentTypes,
    GrapheneComponentTypesOrError,
]
