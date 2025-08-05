from collections.abc import Mapping, Sequence, Set
from typing import TYPE_CHECKING, Optional

from dagster._core.errors import DagsterRunAlreadyExists, DagsterRunConflict
from dagster._core.instance.runs.run_creation import construct_run_with_snapshots
from dagster._core.instance.utils import _check_run_equality, _format_field_diff
from dagster._core.origin import JobPythonOrigin
from dagster._core.storage.dagster_run import DagsterRun, DagsterRunStatus

if TYPE_CHECKING:
    from dagster._core.instance.runs.run_instance_ops import RunInstanceOps
    from dagster._core.snap import ExecutionPlanSnapshot, JobSnap


def register_managed_run(
    ops: "RunInstanceOps",
    job_name: str,
    run_id: str,
    run_config: Optional[Mapping[str, object]],
    resolved_op_selection: Optional[Set[str]],
    step_keys_to_execute: Optional[Sequence[str]],
    tags: Mapping[str, str],
    root_run_id: Optional[str],
    parent_run_id: Optional[str],
    job_snapshot: Optional["JobSnap"],
    execution_plan_snapshot: Optional["ExecutionPlanSnapshot"],
    parent_job_snapshot: Optional["JobSnap"],
    op_selection: Optional[Sequence[str]] = None,
    job_code_origin: Optional[JobPythonOrigin] = None,
) -> DagsterRun:
    """Managed run registration moved from DagsterInstance."""
    # The usage of this method is limited to dagster-airflow, specifically in Dagster
    # Operators that are executed in Airflow. Because a common workflow in Airflow is to
    # retry dags from arbitrary tasks, we need any node to be capable of creating a
    # DagsterRun.
    #
    # The try-except DagsterRunAlreadyExists block handles the race when multiple "root" tasks
    # simultaneously execute self._run_storage.add_run(dagster_run). When this happens, only
    # one task succeeds in creating the run, while the others get DagsterRunAlreadyExists
    # error; at this point, the failed tasks try again to fetch the existing run.
    # https://github.com/dagster-io/dagster/issues/2412

    dagster_run = construct_run_with_snapshots(
        ops,
        job_name=job_name,
        run_id=run_id,
        run_config=run_config,
        op_selection=op_selection,
        resolved_op_selection=resolved_op_selection,
        step_keys_to_execute=step_keys_to_execute,
        status=DagsterRunStatus.MANAGED,
        tags=tags,
        root_run_id=root_run_id,
        parent_run_id=parent_run_id,
        job_snapshot=job_snapshot,
        execution_plan_snapshot=execution_plan_snapshot,
        parent_job_snapshot=parent_job_snapshot,
        job_code_origin=job_code_origin,
    )

    def get_run() -> DagsterRun:
        candidate_run = ops.get_run_by_id(dagster_run.run_id)

        field_diff = _check_run_equality(dagster_run, candidate_run)  # type: ignore  # (possible none)

        if field_diff:
            raise DagsterRunConflict(
                f"Found conflicting existing run with same id {dagster_run.run_id}. Runs differ in:"
                f"\n{_format_field_diff(field_diff)}",
            )
        return candidate_run  # type: ignore  # (possible none)

    if ops.has_run(dagster_run.run_id):
        return get_run()

    try:
        return ops.run_storage.add_run(dagster_run)
    except DagsterRunAlreadyExists:
        return get_run()
