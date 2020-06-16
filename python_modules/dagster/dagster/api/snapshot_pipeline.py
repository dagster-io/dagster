from dagster import check
from dagster.core.host_representation.external_data import ExternalPipelineSubsetResult
from dagster.core.origin import PipelinePythonOrigin

from .utils import execute_unary_api_cli_command


def sync_get_external_pipeline_subset(pipeline_origin, solid_selection=None):
    from dagster.cli.api import PipelineSubsetSnapshotArgs

    check.inst_param(pipeline_origin, 'pipeline_origin', PipelinePythonOrigin)
    check.opt_list_param(solid_selection, 'solid_selection', of_type=str)

    return check.inst(
        execute_unary_api_cli_command(
            pipeline_origin.executable_path,
            'pipeline_subset',
            PipelineSubsetSnapshotArgs(
                pipeline_origin=pipeline_origin, solid_selection=solid_selection
            ),
        ),
        ExternalPipelineSubsetResult,
    )
