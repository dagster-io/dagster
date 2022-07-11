from typing import TYPE_CHECKING, List, Optional

import dagster._check as check
from dagster.core.definitions.events import AssetKey
from dagster.core.errors import DagsterUserCodeProcessError
from dagster.core.host_representation.external_data import ExternalPipelineSubsetResult
from dagster.core.host_representation.origin import ExternalPipelineOrigin
from dagster.grpc.types import PipelineSubsetSnapshotArgs
from dagster.serdes import deserialize_as

if TYPE_CHECKING:
    from dagster.grpc.client import DagsterGrpcClient


def sync_get_external_pipeline_subset_grpc(
    api_client: "DagsterGrpcClient",
    pipeline_origin: ExternalPipelineOrigin,
    solid_selection: Optional[List[str]] = None,
    asset_selection: Optional[List[AssetKey]] = None,
) -> ExternalPipelineSubsetResult:
    from dagster.grpc.client import DagsterGrpcClient

    check.inst_param(api_client, "api_client", DagsterGrpcClient)
    pipeline_origin = check.inst_param(pipeline_origin, "pipeline_origin", ExternalPipelineOrigin)
    solid_selection = check.opt_list_param(solid_selection, "solid_selection", of_type=str)
    asset_selection = check.opt_list_param(asset_selection, "asset_selection", of_type=AssetKey)

    result = deserialize_as(
        api_client.external_pipeline_subset(
            pipeline_subset_snapshot_args=PipelineSubsetSnapshotArgs(
                pipeline_origin=pipeline_origin,
                solid_selection=solid_selection,
                asset_selection=asset_selection,
            ),
        ),
        ExternalPipelineSubsetResult,
    )

    if result.error:
        raise DagsterUserCodeProcessError.from_error_info(result.error)

    return result
