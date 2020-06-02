import json

from dagster import check
from dagster.core.host_representation.external_data import ExternalPipelineSubsetResult
from dagster.core.host_representation.handle import PipelineHandle
from dagster.serdes.ipc import read_unary_response
from dagster.seven import xplat_shlex_split
from dagster.utils.temp_file import get_temp_file_name

from .utils import execute_command_in_subprocess


def sync_get_external_pipeline_subset(pipeline_handle, solid_subset=None):
    check.inst_param(pipeline_handle, 'pipeline_handle', PipelineHandle)
    check.opt_list_param(solid_subset, 'solid_subset', of_type=str)

    location_handle = pipeline_handle.repository_handle.location_handle

    with get_temp_file_name() as output_file:
        parts = (
            ['dagster', 'api', 'snapshot', 'pipeline_subset', output_file]
            + xplat_shlex_split(location_handle.pointer.get_cli_args())
            + [pipeline_handle.pipeline_name]
        )

        if solid_subset:
            parts.append(
                '--solid-subset={solid_subset}'.format(solid_subset=json.dumps(solid_subset))
            )

        execute_command_in_subprocess(parts)

        external_pipeline_subset_result = read_unary_response(output_file)
        check.inst(external_pipeline_subset_result, ExternalPipelineSubsetResult)

        return external_pipeline_subset_result
