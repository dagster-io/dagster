import graphene
from dagster._core.definitions.selector import RepositorySelector
from dagster._core.remote_representation.code_location import GrpcServerCodeLocation
from dagster._core.remote_representation.components import (
    ComponentInstanceSnap,
    ComponentManifest,
    ComponentTypeSnap,
)
from dagster._core.storage.components_storage.types import ComponentChange, ComponentKey
from dagster.components.preview.types import (
    ComponentChangeOperation,
    ComponentInstanceContentsRequest,
)
from dagster_shared.serdes.serdes import serialize_value

from dagster_graphql.implementation.utils import capture_error
from dagster_graphql.schema.errors import GraphenePythonError
from dagster_graphql.schema.inputs import GrapheneRepositorySelector
from dagster_graphql.schema.util import ResolveInfo, non_null_list


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

    def __init__(
        self, repository_selector: RepositorySelector, component_key: ComponentKey, path: list[str]
    ):
        self._repository_selector = repository_selector
        self._component_key = component_key
        super().__init__(path=path, diffInformation=GrapheneComponentFileDiffInformation(0, 0))

    def _resolve_contents_from_grpc(self, graphene_info: ResolveInfo):
        content_request = ComponentInstanceContentsRequest(
            repo_selector=RepositorySelector(
                location_name=self._repository_selector.location_name,
                repository_name=self._repository_selector.repository_name,
            ),
            component_keys=["/".join(self._component_key.path)],
        )
        code_location = graphene_info.context.get_code_location(
            self._repository_selector.location_name
        )
        if not isinstance(code_location, GrpcServerCodeLocation):
            return

        return code_location.client.component_instance_contents(serialize_value(content_request))

    def resolve_contents(self, graphene_info: ResolveInfo):
        instance = graphene_info.context.instance
        repository = graphene_info.context.get_repository(self._repository_selector)
        git_sha = repository.get_display_metadata().get("commit_hash")

        changes = [
            change
            for change in instance.get_component_changes(
                repository_selector=self._repository_selector,
                git_sha=git_sha,
                component_key=self._component_key,
            )
            if change.file_path == self.path
        ]

        if len(changes) == 0:
            return ""

        return instance.get_component_file_from_change(changes[-1])


class GrapheneComponentInstance(graphene.ObjectType):
    """An instance of a component, used to power the components browser and editor experience in the UI."""

    class Meta:
        name = "ComponentInstance"

    path = non_null_list(graphene.String)
    files = non_null_list(GrapheneComponentInstanceFile)

    def __init__(
        self, repository_selector: RepositorySelector, instance_snap: ComponentInstanceSnap
    ):
        self._repository_selector = repository_selector
        super().__init__(
            path=instance_snap.key.split("/"),
            files=[
                GrapheneComponentInstanceFile(
                    self._repository_selector,
                    ComponentKey(path=instance_snap.key.split("/")),
                    ["sample.txt"],
                )
            ],
        )


class GrapheneComponentType(graphene.ObjectType):
    """A type of component, used to power the components browser and editor experience in the UI."""

    class Meta:
        name = "ComponentType"

    key = graphene.NonNull(graphene.String)
    schema = graphene.Field(graphene.String)

    def __init__(self, repository_selector: RepositorySelector, type_snap: ComponentTypeSnap):
        self._repository_selector = repository_selector
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

    def __init__(
        self, repository_selector: RepositorySelector, component_manifest: ComponentManifest
    ):
        self._repository_selector = repository_selector
        super().__init__(
            componentInstances=[
                GrapheneComponentInstance(self._repository_selector, instance_snap)
                for instance_snap in component_manifest.instances
            ],
            componentTypes=[
                GrapheneComponentType(self._repository_selector, type_snap)
                for type_snap in component_manifest.types
            ],
        )


class GrapheneCodeLocationComponentsManifestOrError(graphene.Union):
    class Meta:
        types = (GrapheneCodeLocationComponentsManifest, GraphenePythonError)
        name = "CodeLocationComponentsManifestOrError"


class GrapheneUpdateComponentFileMutation(graphene.Mutation):
    success = graphene.NonNull(graphene.Boolean)

    class Arguments:
        component_path = non_null_list(graphene.String)
        file_path = non_null_list(graphene.String)
        contents = graphene.NonNull(graphene.String)
        repository_selector = graphene.NonNull(GrapheneRepositorySelector)

    class Meta:
        name = "UpdateComponentFileMutation"

    @capture_error
    def mutate(
        self,
        graphene_info: ResolveInfo,
        repository_selector: GrapheneRepositorySelector,
        component_path: list[str],
        file_path: list[str],
        contents: str,
    ):
        instance = graphene_info.context.instance
        component_key = ComponentKey(path=component_path)
        instance.insert_component_change(
            ComponentChange(
                component_key=component_key,
                file_path=file_path,
                operation=ComponentChangeOperation.UPDATE,
                snapshot_sha=instance.upload_component_file(
                    component_key=component_key, file_path=file_path, contents=contents
                ),
                repository_selector=RepositorySelector.from_graphql_input(repository_selector),
            )
        )
        return GrapheneUpdateComponentFileMutation(success=True)
