from collections.abc import Sequence
from typing import Optional

from dagster._core.definitions.selector import RepositorySelector
from dagster._core.storage.components_storage.types import ComponentKey
from dagster_shared import check

from dagster_graphql.schema.components import (
    ComponentChange,
    GrapheneCodeLocationComponentsManifest,
    GrapheneComponentInstance,
    GrapheneComponentPreviewResult,
)
from dagster_graphql.schema.util import ResolveInfo


def fetch_code_location_components_manifest(
    graphene_info: ResolveInfo,
    repository_selector: RepositorySelector,
    with_component_changes: Optional[Sequence[ComponentChange]] = None,
) -> GrapheneCodeLocationComponentsManifest:
    repository = graphene_info.context.get_code_location(
        repository_selector.location_name
    ).get_repository(repository_selector.repository_name)
    snap = repository.repository_snap
    return GrapheneCodeLocationComponentsManifest(
        repository_selector,
        check.not_none(snap.component_manifest),
        with_component_changes=with_component_changes,
    )


def preview_component_changes(
    graphene_info: ResolveInfo,
    repository_selector: RepositorySelector,
    component_path: list[str],
):
    code_location = graphene_info.context.get_code_location(repository_selector.location_name)
    changes = graphene_info.context.instance.get_component_changes(
        repository_selector=repository_selector,
        git_sha=None,
        component_key=ComponentKey(component_path),
    )
    remote_repo = code_location.get_component_instance_preview(
        repository_selector,
        component_keys=[ComponentKey(path=component_path)],
        preview_changes=list(changes),
    )

    return GrapheneComponentPreviewResult(preview_repo=remote_repo)


def fetch_component_instance(
    graphene_info: ResolveInfo,
    repository_selector: RepositorySelector,
    component_id: str,
):
    repository = graphene_info.context.get_code_location(
        repository_selector.location_name
    ).get_repository(repository_selector.repository_name)
    manifest = check.not_none(repository.repository_snap.component_manifest)
    for instance in manifest.instances:
        if component_id == instance.key:
            return GrapheneComponentInstance(
                repository_selector=repository_selector,
                instance_snap=instance,
                with_component_changes=None,
            )

    check.failed(f"Could not find component id {component_id}")
