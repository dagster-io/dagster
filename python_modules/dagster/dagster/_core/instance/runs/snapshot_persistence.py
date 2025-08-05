import warnings
from collections.abc import Sequence
from typing import TYPE_CHECKING, Optional

import dagster._check as check

if TYPE_CHECKING:
    from dagster._core.instance.runs.run_instance_ops import RunInstanceOps
    from dagster._core.snap import ExecutionPlanSnapshot, JobSnap


def ensure_persisted_job_snapshot(
    ops: "RunInstanceOps",
    job_snapshot: "JobSnap",
    parent_job_snapshot: "Optional[JobSnap]",
) -> str:
    """Moved from DagsterInstance._ensure_persisted_job_snapshot."""
    from dagster._core.snap import JobSnap

    check.inst_param(job_snapshot, "job_snapshot", JobSnap)
    check.opt_inst_param(parent_job_snapshot, "parent_job_snapshot", JobSnap)

    if job_snapshot.lineage_snapshot:
        parent_snapshot_id = check.not_none(parent_job_snapshot).snapshot_id

        if job_snapshot.lineage_snapshot.parent_snapshot_id != parent_snapshot_id:
            warnings.warn(
                f"Stored parent snapshot ID {parent_snapshot_id} did not match the parent snapshot ID {job_snapshot.lineage_snapshot.parent_snapshot_id} on the subsetted job"
            )

        if not ops.run_storage.has_job_snapshot(parent_snapshot_id):
            ops.run_storage.add_job_snapshot(check.not_none(parent_job_snapshot))

    job_snapshot_id = job_snapshot.snapshot_id
    if not ops.run_storage.has_job_snapshot(job_snapshot_id):
        returned_job_snapshot_id = ops.run_storage.add_job_snapshot(job_snapshot)
        check.invariant(job_snapshot_id == returned_job_snapshot_id)

    return job_snapshot_id


def ensure_persisted_execution_plan_snapshot(
    ops: "RunInstanceOps",
    execution_plan_snapshot: "ExecutionPlanSnapshot",
    job_snapshot_id: str,
    step_keys_to_execute: Optional[Sequence[str]],
) -> str:
    """Moved from DagsterInstance._ensure_persisted_execution_plan_snapshot."""
    from dagster._core.snap.execution_plan_snapshot import (
        ExecutionPlanSnapshot,
        create_execution_plan_snapshot_id,
    )

    check.inst_param(execution_plan_snapshot, "execution_plan_snapshot", ExecutionPlanSnapshot)
    check.str_param(job_snapshot_id, "job_snapshot_id")
    check.opt_nullable_sequence_param(step_keys_to_execute, "step_keys_to_execute", of_type=str)

    check.invariant(
        execution_plan_snapshot.job_snapshot_id == job_snapshot_id,
        "Snapshot mismatch: Snapshot ID in execution plan snapshot is "
        f'"{execution_plan_snapshot.job_snapshot_id}" and snapshot_id created in memory is '
        f'"{job_snapshot_id}"',
    )

    execution_plan_snapshot_id = create_execution_plan_snapshot_id(execution_plan_snapshot)

    if not ops.run_storage.has_execution_plan_snapshot(execution_plan_snapshot_id):
        returned_execution_plan_snapshot_id = ops.run_storage.add_execution_plan_snapshot(
            execution_plan_snapshot
        )

        check.invariant(execution_plan_snapshot_id == returned_execution_plan_snapshot_id)

    return execution_plan_snapshot_id
