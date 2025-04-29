from typing import Optional

import graphene
from dagster._core.definitions.selector import RepositorySelector
from dagster._core.remote_representation.code_location import GrpcServerCodeLocation
from dagster._core.remote_representation.components import (
    ComponentInstanceSnap,
    ComponentManifest,
    ComponentTypeSnap,
)
from dagster._core.remote_representation.external import RemoteRepository
from dagster._core.storage.components_storage.types import (
    ComponentChange,
    ComponentChangeOperation,
    ComponentKey,
)
from dagster.components.preview.types import (
    ComponentInstanceContentsRequest,
    ComponentInstanceContentsResponse,
)
from dagster_shared.serdes.serdes import deserialize_value, serialize_value

from dagster_graphql.implementation.utils import capture_error
from dagster_graphql.schema.errors import GraphenePythonError
from dagster_graphql.schema.inputs import GrapheneRepositorySelector
from dagster_graphql.schema.util import ResolveInfo, non_null_list


class GrapheneComponentInstanceFile(graphene.ObjectType):
    """A file that is part of a component instance."""

    class Meta:
        name = "ComponentInstanceFile"

    path = non_null_list(graphene.String)
    baseContents = graphene.NonNull(graphene.String)
    currentContents = graphene.NonNull(graphene.String)
    baseSha = graphene.NonNull(graphene.String)
    currentSha = graphene.NonNull(graphene.String)

    def __init__(
        self,
        repository_selector: RepositorySelector,
        component_key: ComponentKey,
        path: list[str],
        base_sha: str,
    ):
        self._repository_selector = repository_selector
        self._component_key = component_key
        super().__init__(path=path, baseSha=base_sha)

    def _most_recent_change(self, graphene_info: ResolveInfo) -> Optional[ComponentChange]:
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
            return None

        return changes[-1]

    def resolve_currentSha(self, graphene_info: ResolveInfo):
        change = self._most_recent_change(graphene_info)
        if change is None:
            return self.baseSha

        return change.snapshot_sha

    def resolve_currentContents(self, graphene_info: ResolveInfo):
        instance = graphene_info.context.instance
        change = self._most_recent_change(graphene_info)

        if change:
            return instance.get_component_file_from_change(change)

        instance_contents = self._resolve_contents_from_grpc(graphene_info)
        if instance_contents and instance_contents.contents:
            return instance_contents.contents[-1].file_contents

        return ""

    def resolve_baseContents(self, graphene_info: ResolveInfo):
        instance_contents = self._resolve_contents_from_grpc(graphene_info)
        if instance_contents and instance_contents.contents:
            return instance_contents.contents[-1].file_contents

        return ""

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

        serialized_resp = code_location.client.component_instance_contents(
            serialize_value(content_request)
        )
        return deserialize_value(serialized_resp, ComponentInstanceContentsResponse)


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
            path=list(instance_snap.key.split("/")),
            files=[
                GrapheneComponentInstanceFile(
                    repository_selector=self._repository_selector,
                    component_key=ComponentKey(path=instance_snap.key.split("/")),
                    path=list(file.file_path),
                    base_sha=file.sha1,
                )
                for file in instance_snap.files
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


class GrapheneComponentPreviewResult(graphene.ObjectType):
    class Meta:
        name = "ComponentPreviewResult"

    # jobs = non_null_list(GrapheneJob)
    # schedules = non_null_list(GrapheneSchedule)
    # sensors = non_null_list(GrapheneSensor)
    assetNodes = non_null_list("dagster_graphql.schema.asset_graph.GrapheneAssetNode")
    assetChecks = non_null_list("dagster_graphql.schema.asset_checks.GrapheneAssetCheck")

    def __init__(self, preview_repo: RemoteRepository):
        self._preview_repo = preview_repo
        super().__init__()

    def resolve_assetNodes(self, graphene_info: ResolveInfo):
        from dagster_graphql.schema.asset_graph import GrapheneAssetNode

        return [
            GrapheneAssetNode(remote_node=node)
            for node in self._preview_repo.asset_graph.asset_nodes
        ]

    def resolve_assetChecks(self, graphene_info: ResolveInfo):
        from dagster_graphql.schema.asset_checks import GrapheneAssetCheck

        return [
            GrapheneAssetCheck(remote_node=node)
            for node in self._preview_repo.asset_graph.remote_asset_check_nodes_by_key.values()
        ]


class GrapheneCodeLocationComponentsManifestOrError(graphene.Union):
    class Meta:
        types = (GrapheneCodeLocationComponentsManifest, GraphenePythonError)
        name = "CodeLocationComponentsManifestOrError"


class GraphenePreviewComponentChangesOrError(graphene.Union):
    class Meta:
        types = (GrapheneComponentPreviewResult, GraphenePythonError)
        name = "PreviewComponentChangesOrError"


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
