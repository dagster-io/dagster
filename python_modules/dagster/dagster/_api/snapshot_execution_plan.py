from collections.abc import Mapping, Sequence
from typing import TYPE_CHECKING, AbstractSet, Any, Optional  # noqa: UP035

import dagster._check as check
from dagster._core.definitions.asset_check_spec import AssetCheckKey
from dagster._core.definitions.events import AssetKey
from dagster._core.errors import DagsterUserCodeProcessError
from dagster._core.execution.plan.state import KnownExecutionState
from dagster._core.instance import DagsterInstance
from dagster._core.remote_representation.external_data import DEFAULT_MODE_NAME
from dagster._core.remote_representation.origin import RemoteJobOrigin
from dagster._core.snap.execution_plan_snapshot import (
    ExecutionPlanSnapshot,
    ExecutionPlanSnapshotErrorData,
)
from dagster._grpc.types import ExecutionPlanSnapshotArgs
from dagster._serdes import deserialize_value

if TYPE_CHECKING:
    from dagster._grpc.client import DagsterGrpcClient


def sync_get_external_execution_plan_grpc(
    api_client: "DagsterGrpcClient",
    job_origin: RemoteJobOrigin,
    run_config: Mapping[str, Any],
    job_snapshot_id: str,
    asset_selection: Optional[AbstractSet[AssetKey]] = None,
    asset_check_selection: Optional[AbstractSet[AssetCheckKey]] = None,
    op_selection: Optional[Sequence[str]] = None,
    step_keys_to_execute: Optional[Sequence[str]] = None,
    known_state: Optional[KnownExecutionState] = None,
    instance: Optional[DagsterInstance] = None,
) -> ExecutionPlanSnapshot:
    from dagster._grpc.client import DagsterGrpcClient

    check.inst_param(api_client, "api_client", DagsterGrpcClient)
    check.inst_param(job_origin, "job_origin", RemoteJobOrigin)
    op_selection = check.opt_sequence_param(op_selection, "op_selection", of_type=str)
    asset_selection = check.opt_nullable_set_param(
        asset_selection, "asset_selection", of_type=AssetKey
    )
    asset_check_selection = check.opt_nullable_set_param(
        asset_check_selection, "asset_check_selection", of_type=AssetCheckKey
    )
    run_config = check.mapping_param(run_config, "run_config", key_type=str)
    check.opt_nullable_sequence_param(step_keys_to_execute, "step_keys_to_execute", of_type=str)
    check.str_param(job_snapshot_id, "job_snapshot_id")
    check.opt_inst_param(known_state, "known_state", KnownExecutionState)
    check.opt_inst_param(instance, "instance", DagsterInstance)

    result = deserialize_value(
        api_client.execution_plan_snapshot(
            execution_plan_snapshot_args=ExecutionPlanSnapshotArgs(
                job_origin=job_origin,
                op_selection=op_selection,
                run_config=run_config,
                mode=DEFAULT_MODE_NAME,
                step_keys_to_execute=step_keys_to_execute,
                job_snapshot_id=job_snapshot_id,
                known_state=known_state,
                instance_ref=instance.get_ref() if instance and instance.is_persistent else None,
                asset_selection=asset_selection,
                asset_check_selection=asset_check_selection,
            )
        ),
        (ExecutionPlanSnapshot, ExecutionPlanSnapshotErrorData),
    )

    if isinstance(result, ExecutionPlanSnapshotErrorData):
        raise DagsterUserCodeProcessError.from_error_info(result.error)
    return result
