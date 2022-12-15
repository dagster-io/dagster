from typing import Dict, Iterator, Mapping, Tuple
from dagster._core.definitions.events import AssetKey
from dagster._core.definitions.run_request import RunRequest
from dagster._core.host_representation.external import ExternalRepository
from dagster._core.host_representation.external_data import ExternalAssetNode
from dagster._core.host_representation.repository_location import RepositoryLocation
from dagster._core.workspace.context import WorkspaceProcessContext, WorkspaceRequestContext

import dagster._check as check

def resolve_asset_selection(context: WorkspaceProcessContext, run_request: RunRequest):
    check.inst(context, WorkspaceProcessContext)
    request_context = context.create_request_context()
    asset_keys = asset_keys

    if run_request.stale_only:
        context.repository_locations
    else:
        return run_request.asset_selection


def get_asset_nodes_by_asset_key(graphene_info) -> Mapping[AssetKey, ExternalAssetNode]:
    """
    If multiple repositories have asset nodes for the same asset key, chooses the asset node that
    has an op.
    """

    asset_nodes_by_asset_key: Dict[AssetKey, ExternalAssetNode] = {}
    for repo_loc, repo, external_asset_node in asset_node_iter(graphene_info):
        preexisting_node = asset_nodes_by_asset_key.get(external_asset_node.asset_key)
        if preexisting_node is None or preexisting_node.is_source:
            asset_nodes_by_asset_key[external_asset_node.asset_key] = external_asset_node
                repo_loc,
                repo,
                external_asset_node,
            )

    return asset_nodes_by_asset_key


def asset_node_iter(
    context: WorkspaceRequestContext,
) -> Iterator[Tuple[RepositoryLocation, ExternalRepository, ExternalAssetNode]]:
    for location in context.repository_locations:
        for repository in location.get_repositories().values():
            for external_asset_node in repository.get_external_asset_nodes():
                yield location, repository, external_asset_node
