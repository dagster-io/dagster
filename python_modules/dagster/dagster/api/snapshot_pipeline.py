from dagster import check
from dagster.core.host_representation import ExternalPipelineOrigin
from dagster.core.host_representation.external_data import ExternalPipelineSubsetResult
from dagster.grpc.types import PipelineSubsetSnapshotArgs


def sync_get_external_pipeline_subset_grpc(api_client, pipeline_origin, solid_selection=None):
    from dagster.grpc.client import DagsterGrpcClient

    check.inst_param(api_client, "api_client", DagsterGrpcClient)
    check.inst_param(pipeline_origin, "pipeline_origin", ExternalPipelineOrigin)
    check.opt_list_param(solid_selection, "solid_selection", of_type=str)

    return check.inst(
        api_client.external_pipeline_subset(
            pipeline_subset_snapshot_args=PipelineSubsetSnapshotArgs(
                pipeline_origin=pipeline_origin, solid_selection=solid_selection
            ),
        ),
        ExternalPipelineSubsetResult,
    )
