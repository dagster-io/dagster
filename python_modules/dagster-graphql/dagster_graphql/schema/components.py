import graphene

from dagster_graphql.schema.errors import GraphenePythonError
from dagster_graphql.schema.util import non_null_list


class GrapheneComponentFileDiffInformation(graphene.ObjectType):
    """Visual information about how many lines were added and removed in a file."""

    class Meta:
        name = "ComponentFileDiffInformation"

    added = graphene.NonNull(graphene.Int)
    removed = graphene.NonNull(graphene.Int)


class GrapheneComponentInstanceFile(graphene.ObjectType):
    """A file that is part of a component instance."""

    class Meta:
        name = "ComponentInstanceFile"

    path = non_null_list(graphene.String)
    diffInformation = graphene.Field(GrapheneComponentFileDiffInformation)
    contents = graphene.NonNull(graphene.String)


class GrapheneComponentInstance(graphene.ObjectType):
    """An instance of a component, used to power the components browser and editor experience in the UI."""

    class Meta:
        name = "ComponentInstance"

    path = non_null_list(graphene.String)
    files = non_null_list(GrapheneComponentInstanceFile)


class GrapheneComponentType(graphene.ObjectType):
    """A type of component, used to power the components browser and editor experience in the UI."""

    class Meta:
        name = "ComponentType"

    key = graphene.NonNull(graphene.String)
    schema = graphene.Field(graphene.String)


class GrapheneCodeLocationComponentsManifest(graphene.ObjectType):
    """Full manifest of all components and component types in the code location.
    Used to power the components browser and editor experience in the UI.
    """

    class Meta:
        name = "CodeLocationComponentsManifest"

    componentInstances = non_null_list(GrapheneComponentInstance)
    componentTypes = non_null_list(GrapheneComponentType)


class GrapheneCodeLocationComponentsManifestOrError(graphene.Union):
    class Meta:
        types = (GrapheneCodeLocationComponentsManifest, GraphenePythonError)
        name = "CodeLocationComponentsManifestOrError"
