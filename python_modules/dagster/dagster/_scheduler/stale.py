from typing import Dict, Iterable, List, Mapping, Optional, Sequence

from dagster._core.definitions.events import AssetKey
from dagster._core.definitions.logical_version import (
    DEFAULT_LOGICAL_VERSION,
    CachingProjectedLogicalVersionResolver,
    LogicalVersion,
    extract_logical_version_from_entry,
)
from dagster._core.definitions.run_request import RunRequest
from dagster._core.host_representation.external import ExternalRepository
from dagster._core.host_representation.external_data import ExternalAssetNode
from dagster._core.instance import DagsterInstance
from dagster._core.workspace.context import WorkspaceProcessContext, WorkspaceRequestContext


def resolve_asset_selection(
    context: WorkspaceProcessContext,
    run_request: RunRequest,
    job_name: str,
) -> Optional[Sequence[AssetKey]]:
    if run_request.stale_assets_only:
        request_context = context.create_request_context()
        repositories = _get_repositories(request_context)
        key_to_node_map = _get_asset_nodes_by_asset_key(repositories)
        print(run_request)
        asset_selection = (
            run_request.asset_selection
            if run_request.asset_selection is not None
            else _get_assets_for_job(job_name, key_to_node_map.values())
        )
        print("ASSET SELECTION: ", asset_selection)
        resolver = CachingProjectedLogicalVersionResolver(
            context.instance, repositories, key_to_node_map
        )
        stale_keys: List[AssetKey] = []
        for asset_key in asset_selection:
            projected_logical_version = resolver.get(asset_key)
            current_logical_version = _get_current_logical_version(
                key_to_node_map[asset_key], context.instance
            )
            if projected_logical_version != current_logical_version:
                stale_keys.append(asset_key)
        return stale_keys
    else:
        return run_request.asset_selection


def _get_repositories(context: WorkspaceRequestContext) -> Sequence[ExternalRepository]:
    return [
        repo for loc in context.repository_locations for repo in loc.get_repositories().values()
    ]


def _get_asset_nodes_by_asset_key(
    repositories: Sequence[ExternalRepository],
) -> Mapping[AssetKey, ExternalAssetNode]:
    """
    If multiple repositories have asset nodes for the same asset key, chooses the asset node that
    has an op.
    """
    asset_nodes_by_asset_key: Dict[AssetKey, ExternalAssetNode] = {}
    for repository in repositories:
        for external_asset_node in repository.get_external_asset_nodes():
            preexisting_node = asset_nodes_by_asset_key.get(external_asset_node.asset_key)
            if preexisting_node is None or preexisting_node.is_source:
                asset_nodes_by_asset_key[external_asset_node.asset_key] = external_asset_node
    return asset_nodes_by_asset_key


def _get_current_logical_version(
    node: ExternalAssetNode, instance: DagsterInstance
) -> Optional[LogicalVersion]:
    event = instance.get_latest_logical_version_record(
        node.asset_key,
        node.is_source,
    )
    if event is None and node.is_source:
        return DEFAULT_LOGICAL_VERSION
    elif event is None:
        return None
    else:
        logical_version = extract_logical_version_from_entry(event.event_log_entry)
        return logical_version or DEFAULT_LOGICAL_VERSION


def _get_assets_for_job(
    job_name: str, all_nodes: Iterable[ExternalAssetNode]
) -> Sequence[AssetKey]:
    print("GETTING ASSETS FOR JOB")
    return [node.asset_key for node in all_nodes if job_name in node.job_names]
