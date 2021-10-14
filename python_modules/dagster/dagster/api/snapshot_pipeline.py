from dagster import check
from dagster.core.errors import DagsterUserCodeProcessError
from dagster.core.host_representation.external_data import ExternalPipelineSubsetResult
from dagster.core.host_representation.origin import ExternalPipelineOrigin
from dagster.grpc.types import PipelineSubsetSnapshotArgs
from dagster.serdes import deserialize_json_to_dagster_namedtuple


def sync_get_external_pipeline_subset_grpc(api_client, pipeline_origin, solid_selection=None):
    from dagster.grpc.client import DagsterGrpcClient

    check.inst_param(api_client, "api_client", DagsterGrpcClient)
    check.inst_param(pipeline_origin, "pipeline_origin", ExternalPipelineOrigin)
    check.opt_list_param(solid_selection, "solid_selection", of_type=str)

    result = check.inst(
        deserialize_json_to_dagster_namedtuple(
            api_client.external_pipeline_subset(
                pipeline_subset_snapshot_args=PipelineSubsetSnapshotArgs(
                    pipeline_origin=pipeline_origin, solid_selection=solid_selection
                ),
            ),
        ),
        ExternalPipelineSubsetResult,
    )

    if result.error:
        raise DagsterUserCodeProcessError.from_error_info(result.error)

    return result
