from dagster import check
from dagster.core.errors import DagsterUserCodeProcessError
from dagster.core.execution.plan.state import KnownExecutionState
from dagster.core.host_representation.origin import ExternalPipelineOrigin
from dagster.core.snap.execution_plan_snapshot import (
    ExecutionPlanSnapshot,
    ExecutionPlanSnapshotErrorData,
)
from dagster.grpc.types import ExecutionPlanSnapshotArgs


def sync_get_external_execution_plan_grpc(
    api_client,
    pipeline_origin,
    run_config,
    mode,
    pipeline_snapshot_id,
    solid_selection=None,
    step_keys_to_execute=None,
    known_state=None,
):
    from dagster.grpc.client import DagsterGrpcClient

    check.inst_param(api_client, "api_client", DagsterGrpcClient)
    check.inst_param(pipeline_origin, "pipeline_origin", ExternalPipelineOrigin)
    check.opt_list_param(solid_selection, "solid_selection", of_type=str)
    check.dict_param(run_config, "run_config")
    check.str_param(mode, "mode")
    check.opt_list_param(step_keys_to_execute, "step_keys_to_execute", of_type=str)
    check.str_param(pipeline_snapshot_id, "pipeline_snapshot_id")
    check.opt_inst_param(known_state, "known_state", KnownExecutionState)

    result = check.inst(
        api_client.execution_plan_snapshot(
            execution_plan_snapshot_args=ExecutionPlanSnapshotArgs(
                pipeline_origin=pipeline_origin,
                solid_selection=solid_selection,
                run_config=run_config,
                mode=mode,
                step_keys_to_execute=step_keys_to_execute,
                pipeline_snapshot_id=pipeline_snapshot_id,
                known_state=known_state,
            )
        ),
        (ExecutionPlanSnapshot, ExecutionPlanSnapshotErrorData),
    )

    if isinstance(result, ExecutionPlanSnapshotErrorData):
        raise DagsterUserCodeProcessError.from_error_info(result.error)
    return result
