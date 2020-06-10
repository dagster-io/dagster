from dagster import check
from dagster.core.origin import PipelinePythonOrigin
from dagster.core.snap.execution_plan_snapshot import ExecutionPlanSnapshot
from dagster.serdes.ipc import read_unary_response, write_unary_input
from dagster.utils.temp_file import get_temp_file_name

from .utils import execute_command_in_subprocess


def sync_get_external_execution_plan(
    pipeline_origin,
    environment_dict,
    mode,
    snapshot_id,
    solid_selection=None,
    step_keys_to_execute=None,
):
    from dagster.cli.api import ExecutionPlanSnapshotArgs

    check.inst_param(pipeline_origin, 'pipeline_origin', PipelinePythonOrigin)
    check.opt_list_param(solid_selection, 'solid_selection', of_type=str)
    check.dict_param(environment_dict, 'environment_dict')
    check.str_param(mode, 'mode')
    check.opt_list_param(step_keys_to_execute, 'step_keys_to_execute', of_type=str)
    check.str_param(snapshot_id, 'snapshot_id')

    execute_plan_snapshot_args = ExecutionPlanSnapshotArgs(
        pipeline_origin=pipeline_origin,
        solid_selection=solid_selection,
        environment_dict=environment_dict,
        mode=mode,
        step_keys_to_execute=step_keys_to_execute,
        snapshot_id=snapshot_id,
    )

    with get_temp_file_name() as input_file, get_temp_file_name() as output_file:
        write_unary_input(input_file, execute_plan_snapshot_args)
        parts = [
            pipeline_origin.executable_path,
            '-m',
            'dagster',
            'api',
            'snapshot',
            'execution_plan',
            input_file,
            output_file,
        ]

        execute_command_in_subprocess(parts)

        execution_plan_snapshot = read_unary_response(output_file)
        check.inst(execution_plan_snapshot, ExecutionPlanSnapshot)

        return execution_plan_snapshot
