from dagster import check
from dagster.core.host_representation.external_data import ExternalPipelineSubsetResult
from dagster.core.origin import PipelineOrigin, PipelinePythonOrigin
from dagster.grpc.types import PipelineSubsetSnapshotArgs

from .utils import execute_unary_api_cli_command


def sync_get_external_pipeline_subset(pipeline_origin, solid_selection=None):
    check.inst_param(pipeline_origin, "pipeline_origin", PipelinePythonOrigin)
    check.opt_list_param(solid_selection, "solid_selection", of_type=str)

    return check.inst(
        execute_unary_api_cli_command(
            pipeline_origin.executable_path,
            "pipeline_subset",
            PipelineSubsetSnapshotArgs(
                pipeline_origin=pipeline_origin, solid_selection=solid_selection
            ),
        ),
        ExternalPipelineSubsetResult,
    )


def sync_get_external_pipeline_subset_grpc(api_client, pipeline_origin, solid_selection=None):
    from dagster.grpc.client import DagsterGrpcClient

    check.inst_param(api_client, "api_client", DagsterGrpcClient)
    check.inst_param(pipeline_origin, "pipeline_origin", PipelineOrigin)
    check.opt_list_param(solid_selection, "solid_selection", of_type=str)

    return check.inst(
        api_client.external_pipeline_subset(
            pipeline_subset_snapshot_args=PipelineSubsetSnapshotArgs(
                pipeline_origin=pipeline_origin, solid_selection=solid_selection
            ),
        ),
        ExternalPipelineSubsetResult,
    )
