from typing import TYPE_CHECKING, Any, FrozenSet, List, Mapping, Optional

import dagster._check as check
from dagster.core.definitions.events import AssetKey
from dagster.core.errors import DagsterUserCodeProcessError
from dagster.core.execution.plan.state import KnownExecutionState
from dagster.core.host_representation.origin import ExternalPipelineOrigin
from dagster.core.instance import DagsterInstance
from dagster.core.snap.execution_plan_snapshot import (
    ExecutionPlanSnapshot,
    ExecutionPlanSnapshotErrorData,
)
from dagster.grpc.types import ExecutionPlanSnapshotArgs
from dagster.serdes import deserialize_as

if TYPE_CHECKING:
    from dagster.grpc.client import DagsterGrpcClient


def sync_get_external_execution_plan_grpc(
    api_client: "DagsterGrpcClient",
    pipeline_origin: ExternalPipelineOrigin,
    run_config: Mapping[str, Any],
    mode: str,
    pipeline_snapshot_id: str,
    asset_selection: Optional[FrozenSet[AssetKey]] = None,
    solid_selection: Optional[List[str]] = None,
    step_keys_to_execute: Optional[List[str]] = None,
    known_state: Optional[KnownExecutionState] = None,
    instance: Optional[DagsterInstance] = None,
) -> ExecutionPlanSnapshot:
    from dagster.grpc.client import DagsterGrpcClient

    check.inst_param(api_client, "api_client", DagsterGrpcClient)
    check.inst_param(pipeline_origin, "pipeline_origin", ExternalPipelineOrigin)
    solid_selection = check.opt_list_param(solid_selection, "solid_selection", of_type=str)
    asset_selection = check.opt_set_param(asset_selection, "asset_selection", of_type=AssetKey)
    run_config = check.dict_param(run_config, "run_config", key_type=str)
    check.str_param(mode, "mode")
    check.opt_nullable_list_param(step_keys_to_execute, "step_keys_to_execute", of_type=str)
    check.str_param(pipeline_snapshot_id, "pipeline_snapshot_id")
    check.opt_inst_param(known_state, "known_state", KnownExecutionState)
    check.opt_inst_param(instance, "instance", DagsterInstance)

    result = deserialize_as(
        api_client.execution_plan_snapshot(
            execution_plan_snapshot_args=ExecutionPlanSnapshotArgs(
                pipeline_origin=pipeline_origin,
                solid_selection=solid_selection,
                run_config=run_config,
                mode=mode,
                step_keys_to_execute=step_keys_to_execute,
                pipeline_snapshot_id=pipeline_snapshot_id,
                known_state=known_state,
                instance_ref=instance.get_ref() if instance and instance.is_persistent else None,
                asset_selection=asset_selection,
            )
        ),
        (ExecutionPlanSnapshot, ExecutionPlanSnapshotErrorData),
    )

    if isinstance(result, ExecutionPlanSnapshotErrorData):
        raise DagsterUserCodeProcessError.from_error_info(result.error)
    return result
