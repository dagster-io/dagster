from typing import List, Sequence, Union

import dagster._check as check
from dagster._core.definitions.data_version import (
    CachingStaleStatusResolver,
    StaleStatus,
)
from dagster._core.definitions.events import AssetKey
from dagster._core.definitions.external_asset_graph import ExternalAssetGraph
from dagster._core.definitions.run_request import RunRequest
from dagster._core.host_representation.external import (
    ExternalSchedule,
    ExternalSensor,
)
from dagster._core.workspace.context import WorkspaceProcessContext


def resolve_stale_or_missing_assets(
    context: WorkspaceProcessContext,
    run_request: RunRequest,
    instigator: Union[ExternalSensor, ExternalSchedule],
) -> Sequence[AssetKey]:
    asset_graph = ExternalAssetGraph.from_workspace(context.create_request_context())
    asset_selection = (
        run_request.asset_selection
        if run_request.asset_selection is not None
        else asset_graph.get_materialization_asset_keys_for_job(check.not_none(instigator.job_name))
    )
    resolver = CachingStaleStatusResolver(context.instance, asset_graph)
    stale_or_unknown_keys: List[AssetKey] = []
    for asset_key in asset_selection:
        if resolver.get_status(asset_key) in [StaleStatus.STALE, StaleStatus.MISSING]:
            stale_or_unknown_keys.append(asset_key)
    return stale_or_unknown_keys
