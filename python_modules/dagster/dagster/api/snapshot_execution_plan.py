import json

from dagster import check
from dagster.core.host_representation.handle import PipelineHandle
from dagster.core.snap.execution_plan_snapshot import ExecutionPlanSnapshot
from dagster.serdes.ipc import read_unary_response
from dagster.seven import xplat_shlex_split
from dagster.utils.temp_file import get_temp_file_name

from .utils import execute_command_in_subprocess


def sync_get_external_execution_plan(
    pipeline_handle,
    environment_dict,
    mode,
    snapshot_id,
    solid_subset=None,
    step_keys_to_execute=None,
):
    check.inst_param(pipeline_handle, 'pipeline_handle', PipelineHandle)
    check.opt_list_param(solid_subset, 'solid_subset', of_type=str)
    check.dict_param(environment_dict, 'environment_dict')
    check.str_param(mode, 'mode')
    check.opt_list_param(step_keys_to_execute, 'step_keys_to_execute', of_type=str)
    check.str_param(snapshot_id, 'snapshot_id')

    location_handle = pipeline_handle.repository_handle.repository_location_handle

    with get_temp_file_name() as output_file:
        parts = (
            ['dagster', 'api', 'snapshot', 'execution_plan', output_file]
            + xplat_shlex_split(location_handle.pointer.get_cli_args())
            + [
                pipeline_handle.pipeline_name,
                '--environment-dict={environment_dict}'.format(
                    environment_dict=json.dumps(environment_dict)
                ),
                '--mode={mode}'.format(mode=mode),
                '--snapshot-id={snapshot_id}'.format(snapshot_id=snapshot_id),
            ]
        )

        if solid_subset:
            parts.append(
                '--solid-subset={solid_subset}'.format(solid_subset=json.dumps(solid_subset))
            )

        if step_keys_to_execute:
            parts.append(
                '--step-keys-to-execute={step_keys_to_execute}'.format(
                    step_keys_to_execute=json.dumps(step_keys_to_execute)
                )
            )

        execute_command_in_subprocess(parts)

        execution_plan_snapshot = read_unary_response(output_file)
        check.inst(execution_plan_snapshot, ExecutionPlanSnapshot)

        return execution_plan_snapshot
