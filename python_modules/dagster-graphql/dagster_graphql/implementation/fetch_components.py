from typing import cast

from dagster._core.definitions.selector import RepositorySelector
from dagster._core.remote_representation.code_location import GrpcServerCodeLocation
from dagster._core.remote_representation.external import RemoteRepository
from dagster._core.remote_representation.handle import RepositoryHandle
from dagster._core.storage.components_storage.types import ComponentKey
from dagster.components.preview.types import (
    ComponentInstancePreviewRequest,
    ComponentInstancePreviewResponse,
)
from dagster_shared import check
from dagster_shared.serdes import serialize_value
from dagster_shared.serdes.serdes import deserialize_value

from dagster_graphql.schema.components import (
    GrapheneCodeLocationComponentsManifest,
    GrapheneComponentPreviewResult,
)
from dagster_graphql.schema.util import ResolveInfo


def fetch_code_location_components_manifest(
    graphene_info: ResolveInfo,
    repository_selector: RepositorySelector,
) -> GrapheneCodeLocationComponentsManifest:
    repository = graphene_info.context.get_code_location(
        repository_selector.location_name
    ).get_repository(repository_selector.repository_name)
    snap = repository.repository_snap
    return GrapheneCodeLocationComponentsManifest(
        repository_selector, check.not_none(snap.component_manifest)
    )


def preview_component_changes(
    graphene_info: ResolveInfo,
    repository_selector: RepositorySelector,
    component_path: list[str],
):
    code_location = graphene_info.context.get_code_location(repository_selector.location_name)
    code_location = cast("GrpcServerCodeLocation", code_location)
    changes = graphene_info.context.instance.get_component_changes(
        repository_selector=repository_selector,
        git_sha=None,
        component_key=ComponentKey(component_path),
    )
    request = ComponentInstancePreviewRequest(
        repo_selector=repository_selector,
        component_keys=["/".join(component_path)],
        preview_changes=list(changes),
    )
    serialized_resp = code_location.client.component_instance_preview(serialize_value(request))
    preview = deserialize_value(serialized_resp, ComponentInstancePreviewResponse)

    return GrapheneComponentPreviewResult(
        preview_repo=RemoteRepository(
            preview.defs_snapshot,
            RepositoryHandle.from_location(
                repository_name=repository_selector.repository_name,
                code_location=code_location,
            ),
            auto_materialize_use_sensors=False,  # should not matter
        )
    )
