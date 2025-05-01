import graphene
from dagster._core.remote_representation.components import (
    ComponentInstanceSnap,
    ComponentManifest,
    ComponentTypeSnap,
)

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

    def __init__(self, instance_snap: ComponentInstanceSnap):
        super().__init__(
            path=instance_snap.key.split("/"),
            files=[],
        )


class GrapheneComponentType(graphene.ObjectType):
    """A type of component, used to power the components browser and editor experience in the UI."""

    class Meta:
        name = "ComponentType"

    key = graphene.NonNull(graphene.String)
    schema = graphene.Field(graphene.String)

    def __init__(self, type_snap: ComponentTypeSnap):
        super().__init__(
            key=type_snap.name,
            schema="",
        )


class GrapheneCodeLocationComponentsManifest(graphene.ObjectType):
    """Full manifest of all components and component types in the code location.
    Used to power the components browser and editor experience in the UI.
    """

    class Meta:
        name = "CodeLocationComponentsManifest"

    componentInstances = non_null_list(GrapheneComponentInstance)
    componentTypes = non_null_list(GrapheneComponentType)

    def __init__(self, component_manifest: ComponentManifest):
        super().__init__(
            componentInstances=[
                GrapheneComponentInstance(instance_snap)
                for instance_snap in component_manifest.instances
            ],
            componentTypes=[
                GrapheneComponentType(type_snap) for type_snap in component_manifest.types
            ],
        )


class GrapheneCodeLocationComponentsManifestOrError(graphene.Union):
    class Meta:
        types = (GrapheneCodeLocationComponentsManifest, GraphenePythonError)
        name = "CodeLocationComponentsManifestOrError"
