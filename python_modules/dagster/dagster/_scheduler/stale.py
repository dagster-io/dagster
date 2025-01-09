from collections.abc import Sequence
from typing import Union

import dagster._check as check
from dagster._core.definitions.data_version import CachingStaleStatusResolver, StaleStatus
from dagster._core.definitions.events import AssetKey
from dagster._core.definitions.run_request import RunRequest
from dagster._core.remote_representation.external import RemoteSchedule, RemoteSensor
from dagster._core.workspace.context import WorkspaceProcessContext


def resolve_stale_or_missing_assets(
    context: WorkspaceProcessContext,
    run_request: RunRequest,
    instigator: Union[RemoteSensor, RemoteSchedule],
) -> Sequence[AssetKey]:
    request_context = context.create_request_context()
    asset_graph = request_context.asset_graph
    asset_selection = (
        run_request.asset_selection
        if run_request.asset_selection is not None
        else asset_graph.get_materialization_asset_keys_for_job(check.not_none(instigator.job_name))
    )
    resolver = CachingStaleStatusResolver(context.instance, asset_graph, request_context)
    stale_or_unknown_keys: list[AssetKey] = []
    for asset_key in asset_selection:
        if resolver.get_status(asset_key) in [StaleStatus.STALE, StaleStatus.MISSING]:
            stale_or_unknown_keys.append(asset_key)
    return stale_or_unknown_keys
