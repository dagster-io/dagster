import sys
from collections.abc import Mapping, Sequence
from typing import NamedTuple, Optional, Union

import dagster._check as check
from dagster._core.definitions.run_request import RunRequest
from dagster._core.definitions.selector import JobSubsetSelector
from dagster._core.instance import DagsterInstance
from dagster._core.remote_representation.code_location import CodeLocation
from dagster._core.remote_representation.external import RemoteJob, RemoteSchedule, RemoteSensor
from dagster._core.remote_representation.external_data import TargetSnap
from dagster._core.storage.dagster_run import DagsterRun, DagsterRunStatus, RunsFilter
from dagster._core.storage.tags import RUN_KEY_TAG
from dagster._core.telemetry import SCHEDULED_RUN_CREATED, SENSOR_RUN_CREATED, hash_name, log_action
from dagster._core.workspace.context import IWorkspaceProcessContext
from dagster._daemon.utils import DaemonErrorCapture
from dagster._utils import check_for_debug_crash
from dagster._utils.error import SerializableErrorInfo


class SkippedSensorRun(NamedTuple):
    """Placeholder for runs that are skipped during the run_key idempotence check."""

    run_key: Optional[str]
    existing_run: DagsterRun


class BackfillSubmission(NamedTuple):
    """Placeholder for launched backfills."""

    backfill_id: str


class SubmitRunRequestResult(NamedTuple):
    run_key: Optional[str]
    error_info: Optional[SerializableErrorInfo]
    run: Union[SkippedSensorRun, DagsterRun, BackfillSubmission]


def fetch_existing_runs_for_instigator(
    instance: DagsterInstance,
    remote_instigator: Union[RemoteSensor, RemoteSchedule],
    run_requests: Sequence[RunRequest],
    additional_tags: Mapping[str, str],
) -> dict[str, DagsterRun]:
    run_keys = [run_request.run_key for run_request in run_requests if run_request.run_key]

    if not run_keys:
        return {}

    # fetch runs from the DB with only the run key tag
    # note: while possible to filter more at DB level with tags - it is avoided here due to observed
    # perf problems
    runs_with_run_keys: list[DagsterRun] = []
    for run_key in run_keys:
        # do serial fetching, which has better perf than a single query with an IN clause, due to
        # how the query planner does the runs/run_tags join
        runs_with_run_keys.extend(
            instance.get_runs(filters=RunsFilter(tags={RUN_KEY_TAG: run_key, **additional_tags}))
        )

    # filter down to runs with run_key that match the sensor name and its namespace (repository)
    valid_runs: list[DagsterRun] = []
    for run in runs_with_run_keys:
        # if the run doesn't have a set origin, consider it a match, since it matches on the
        # additional tags set in the query
        if run.remote_job_origin is None:
            valid_runs.append(run)
        # otherwise prevent the same named instigator across repos from effecting each other
        elif (
            run.remote_job_origin.repository_origin.get_selector()
            == remote_instigator.get_remote_origin().repository_origin.get_selector()
        ):
            valid_runs.append(run)

    existing_runs: dict[str, DagsterRun] = {}
    for run in valid_runs:
        tags = run.tags or {}
        # Guaranteed to have non-null run key because the source set of runs is `runs_with_run_keys`
        # above.
        run_key = check.not_none(tags.get(RUN_KEY_TAG))
        existing_runs[run_key] = run

    return existing_runs


def get_code_location_for_instigator(
    workspace_process_context: IWorkspaceProcessContext,
    remote_instigator: Union[RemoteSensor, RemoteSchedule],
) -> CodeLocation:
    origin = remote_instigator.get_remote_origin()
    return workspace_process_context.create_request_context().get_code_location(
        origin.repository_origin.code_location_origin.location_name
    )


def _create_instigator_run(
    instance: DagsterInstance,
    code_location: CodeLocation,
    remote_instigator: Union[RemoteSensor, RemoteSchedule],
    remote_job: RemoteJob,
    run_id: str,
    run_request: RunRequest,
    target_data: TargetSnap,
    additional_tags: Mapping[str, str],
) -> DagsterRun:
    from dagster._daemon.daemon import get_telemetry_daemon_session_id

    remote_execution_plan = code_location.get_execution_plan(
        remote_job,
        run_request.run_config,
        step_keys_to_execute=None,
        known_state=None,
        instance=instance,
    )
    execution_plan_snapshot = remote_execution_plan.execution_plan_snapshot

    tags = {
        **(remote_job.run_tags or {}),
        **run_request.tags,
        **additional_tags,
    }
    if run_request.run_key:
        tags[RUN_KEY_TAG] = run_request.run_key

    action = (
        SENSOR_RUN_CREATED if isinstance(remote_instigator, RemoteSensor) else SCHEDULED_RUN_CREATED
    )
    name_meta_key = (
        "SENSOR_NAME_HASH" if isinstance(remote_instigator, RemoteSensor) else "SCHEDULE_NAME_HASH"
    )

    log_action(
        instance,
        action,
        metadata={
            "DAEMON_SESSION_ID": get_telemetry_daemon_session_id(),
            "pipeline_name_hash": hash_name(remote_job.name),
            "repo_hash": hash_name(code_location.name),
            name_meta_key: hash_name(remote_instigator.name),
        },
    )

    return instance.create_run(
        job_name=target_data.job_name,
        run_id=run_id,
        run_config=run_request.run_config,
        resolved_op_selection=remote_job.resolved_op_selection,
        step_keys_to_execute=None,
        status=DagsterRunStatus.NOT_STARTED,
        op_selection=target_data.op_selection,
        root_run_id=None,
        parent_run_id=None,
        tags=tags,
        job_snapshot=remote_job.job_snapshot,
        execution_plan_snapshot=execution_plan_snapshot,
        parent_job_snapshot=remote_job.parent_job_snapshot,
        remote_job_origin=remote_job.get_remote_origin(),
        job_code_origin=remote_job.get_python_origin(),
        asset_selection=(
            frozenset(run_request.asset_selection) if run_request.asset_selection else None
        ),
        asset_check_selection=(
            frozenset(run_request.asset_check_keys) if run_request.asset_check_keys else None
        ),
        asset_graph=code_location.get_repository(
            remote_job.repository_handle.repository_name
        ).asset_graph,
    )


def submit_instigator_run_request(
    run_id: str,
    run_request: RunRequest,
    workspace_process_context: IWorkspaceProcessContext,
    remote_instigator: Union[RemoteSensor, RemoteSchedule],
    target_data: TargetSnap,
    existing_runs_by_key: dict[str, DagsterRun],
    logger,
    additional_tags: Mapping[str, str],
    debug_crash_flags,
) -> SubmitRunRequestResult:
    instance = workspace_process_context.instance
    schedule_origin = remote_instigator.get_remote_origin()

    run_key = run_request.run_key
    run = (run_key and existing_runs_by_key.get(run_key)) or instance.get_run_by_id(run_id)

    if run:
        if run.status != DagsterRunStatus.NOT_STARTED:
            # A run already exists and was launched for this run key, but the daemon must have
            # crashed before the tick could be updated
            return SubmitRunRequestResult(
                run_key=run_key,
                error_info=None,
                run=SkippedSensorRun(run_key=run_request.run_key, existing_run=run),
            )
        else:
            logger.info(
                f"Run {run.run_id} already created with the run key "
                f"`{run_key}` for {remote_instigator.name}"
            )

    else:
        job_subset_selector = JobSubsetSelector(
            location_name=schedule_origin.repository_origin.code_location_origin.location_name,
            repository_name=schedule_origin.repository_origin.repository_name,
            job_name=target_data.job_name,
            op_selection=target_data.op_selection,
            asset_selection=run_request.asset_selection,
            asset_check_selection=run_request.asset_check_keys,
        )

        # reload the code_location on each submission, request_context derived data can become out date
        # * non-threaded: if number of serial submissions is too many
        # * threaded: if thread sits pending in pool too long
        code_location = get_code_location_for_instigator(
            workspace_process_context, remote_instigator
        )

        remote_job = code_location.get_job(job_subset_selector)

        run = _create_instigator_run(
            instance=instance,
            code_location=code_location,
            remote_instigator=remote_instigator,
            remote_job=remote_job,
            run_request=run_request,
            run_id=run_id,
            target_data=target_data,
            additional_tags=additional_tags,
        )

        if run_key:
            existing_runs_by_key[run_key] = run

    check_for_debug_crash(debug_crash_flags, "RUN_CREATED")

    error_info = None
    try:
        logger.info(f"Launching run for {remote_instigator.name}")
        instance.submit_run(run.run_id, workspace_process_context.create_request_context())
        logger.info(f"Completed launch of run {run.run_id} for {remote_instigator.name}")
    except Exception:
        error_info = DaemonErrorCapture.process_exception(
            exc_info=sys.exc_info(),
            logger=logger,
            log_message=f"Run {run.run_id} created successfully but failed to launch",
        )

    check_for_debug_crash(debug_crash_flags, "RUN_LAUNCHED")
    return SubmitRunRequestResult(run_key=run_request.run_key, error_info=error_info, run=run)
