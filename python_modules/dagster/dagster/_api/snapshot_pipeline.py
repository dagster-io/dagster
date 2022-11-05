from typing import TYPE_CHECKING, Optional, Sequence

import dagster._check as check
from dagster._core.definitions.events import AssetKey
from dagster._core.errors import DagsterUserCodeProcessError
from dagster._core.host_representation.external_data import ExternalPipelineSubsetResult
from dagster._core.host_representation.origin import ExternalPipelineOrigin
from dagster._grpc.types import PipelineSubsetSnapshotArgs
from dagster._serdes import deserialize_as

if TYPE_CHECKING:
    from dagster._grpc.client import DagsterGrpcClient


def sync_get_external_pipeline_subset_grpc(
    api_client: "DagsterGrpcClient",
    pipeline_origin: ExternalPipelineOrigin,
    solid_selection: Optional[Sequence[str]] = None,
    asset_selection: Optional[Sequence[AssetKey]] = None,
) -> ExternalPipelineSubsetResult:
    from dagster._grpc.client import DagsterGrpcClient

    check.inst_param(api_client, "api_client", DagsterGrpcClient)
    pipeline_origin = check.inst_param(pipeline_origin, "pipeline_origin", ExternalPipelineOrigin)
    solid_selection = check.opt_sequence_param(solid_selection, "solid_selection", of_type=str)
    asset_selection = check.opt_sequence_param(asset_selection, "asset_selection", of_type=AssetKey)

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
