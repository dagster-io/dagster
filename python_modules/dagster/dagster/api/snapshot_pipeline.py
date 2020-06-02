import json

from dagster import check
from dagster.core.host_representation.external_data import ExternalPipelineSubsetResult
from dagster.core.host_representation.handle import (
    PipelineHandle,
    PythonEnvRepositoryLocationHandle,
)
from dagster.serdes.ipc import read_unary_response
from dagster.seven import xplat_shlex_split
from dagster.utils.temp_file import get_temp_file_name

from .utils import execute_command_in_subprocess


def sync_get_external_pipeline_subset(pipeline_handle, solid_selection=None):
    check.inst_param(pipeline_handle, 'pipeline_handle', PipelineHandle)
    check.opt_list_param(solid_selection, 'solid_selection', of_type=str)

    location_handle = pipeline_handle.repository_handle.repository_location_handle
    check.param_invariant(
        isinstance(location_handle, PythonEnvRepositoryLocationHandle), 'pipeline_handle'
    )

    pointer = pipeline_handle.repository_handle.get_pointer()
    with get_temp_file_name() as output_file:
        parts = (
            [
                location_handle.executable_path,
                '-m',
                'dagster',
                'api',
                'snapshot',
                'pipeline_subset',
                output_file,
            ]
            + xplat_shlex_split(pointer.get_cli_args())
            + [pipeline_handle.pipeline_name]
        )

        if solid_selection:
            parts.append(
                '--solid-subset={solid_selection}'.format(
                    solid_selection=json.dumps(solid_selection)
                )
            )

        execute_command_in_subprocess(parts)

        external_pipeline_subset_result = read_unary_response(output_file)
        check.inst(external_pipeline_subset_result, ExternalPipelineSubsetResult)

        return external_pipeline_subset_result
