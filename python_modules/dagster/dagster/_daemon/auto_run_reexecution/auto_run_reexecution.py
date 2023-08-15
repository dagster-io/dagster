import sys
from typing import Iterator, Optional, Sequence, Tuple, cast

from dagster._core.definitions.metadata import MetadataValue
from dagster._core.definitions.selector import JobSubsetSelector
from dagster._core.events import EngineEventData
from dagster._core.execution.plan.resume_retry import ReexecutionStrategy
from dagster._core.instance import DagsterInstance
from dagster._core.storage.dagster_run import DagsterRun, DagsterRunStatus, RunRecord
from dagster._core.storage.tags import MAX_RETRIES_TAG, RETRY_NUMBER_TAG, RETRY_STRATEGY_TAG
from dagster._core.workspace.context import IWorkspaceProcessContext
from dagster._utils.error import serializable_error_info_from_exc_info

DEFAULT_REEXECUTION_POLICY = ReexecutionStrategy.FROM_FAILURE


def filter_runs_to_should_retry(
    runs: Sequence[DagsterRun], instance: DagsterInstance, default_max_retries: int
) -> Iterator[Tuple[DagsterRun, int]]:
    """Return only runs that should retry along with their retry number (1st retry, 2nd, etc.)."""

    def get_retry_number(run: DagsterRun) -> Optional[int]:
        if run.status != DagsterRunStatus.FAILURE:
            return None

        raw_max_retries_tag = run.tags.get(MAX_RETRIES_TAG)
        if raw_max_retries_tag is None:
            max_retries = default_max_retries
        else:
            try:
                max_retries = int(raw_max_retries_tag)
            except ValueError:
                instance.report_engine_event(
                    f"Error parsing int from tag {MAX_RETRIES_TAG}, won't retry the run.", run
                )
                return None

        if max_retries == 0:
            return None

        # TODO: group these to reduce db calls
        run_group = instance.get_run_group(run.run_id)

        if run_group:
            _, run_group_iter = run_group
            run_group_list = list(run_group_iter)

            # Has the parent run already been retried the maximum number of times? (Group includes the parent)
            if len(run_group_list) >= max_retries + 1:
                return None

            # Does this run already have a child run?
            if any([run.run_id == run_.parent_run_id for run_ in run_group_list]):
                return None
            return len(run_group_list)
        else:
            return 1

    for run in runs:
        retry_number = get_retry_number(run)
        if retry_number is not None:
            yield (run, retry_number)


def get_reexecution_strategy(
    run: DagsterRun, instance: DagsterInstance
) -> Optional[ReexecutionStrategy]:
    raw_strategy_tag = run.tags.get(RETRY_STRATEGY_TAG)
    if raw_strategy_tag is None:
        return None

    if raw_strategy_tag not in ReexecutionStrategy.__members__:
        instance.report_engine_event(
            f"Error parsing retry strategy from tag '{RETRY_STRATEGY_TAG}: {raw_strategy_tag}'", run
        )
        return None
    else:
        return ReexecutionStrategy[raw_strategy_tag]


def retry_run(
    failed_run: DagsterRun,
    retry_number: int,
    workspace_context: IWorkspaceProcessContext,
) -> None:
    """Submit a retry as a re-execute from failure."""
    instance = workspace_context.instance
    tags = {RETRY_NUMBER_TAG: str(retry_number)}
    workspace = workspace_context.create_request_context()
    if not failed_run.external_job_origin:
        instance.report_engine_event(
            "Run does not have an external job origin, unable to retry the run.",
            failed_run,
        )
        return

    origin = failed_run.external_job_origin.external_repository_origin
    code_location = workspace.get_code_location(origin.code_location_origin.location_name)
    repo_name = origin.repository_name

    if not code_location.has_repository(repo_name):
        instance.report_engine_event(
            f"Could not find repository {repo_name} in location {code_location.name}, unable to"
            " retry the run. It was likely renamed or deleted.",
            failed_run,
        )
        return

    external_repo = code_location.get_repository(repo_name)

    if not external_repo.has_external_job(failed_run.job_name):
        instance.report_engine_event(
            f"Could not find job {failed_run.job_name} in repository {repo_name}, unable"
            " to retry the run. It was likely renamed or deleted.",
            failed_run,
        )
        return

    external_job = code_location.get_external_job(
        JobSubsetSelector(
            location_name=origin.code_location_origin.location_name,
            repository_name=repo_name,
            job_name=failed_run.job_name,
            op_selection=failed_run.op_selection,
            asset_selection=(
                None if failed_run.asset_selection is None else list(failed_run.asset_selection)
            ),
        )
    )

    strategy = get_reexecution_strategy(failed_run, instance) or DEFAULT_REEXECUTION_POLICY

    new_run = instance.create_reexecuted_run(
        parent_run=failed_run,
        code_location=code_location,
        external_job=external_job,
        strategy=strategy,
        extra_tags=tags,
        use_parent_run_tags=True,
    )

    instance.report_engine_event(
        "Retrying the run",
        failed_run,
        engine_event_data=EngineEventData({"new run": MetadataValue.dagster_run(new_run.run_id)}),
    )
    instance.report_engine_event(
        "Launched as an automatic retry",
        new_run,
        engine_event_data=EngineEventData(
            {"failed run": MetadataValue.dagster_run(failed_run.run_id)}
        ),
    )

    instance.submit_run(new_run.run_id, workspace)


def consume_new_runs_for_automatic_reexecution(
    workspace_process_context: IWorkspaceProcessContext,
    run_records: Sequence[RunRecord],
) -> Iterator[None]:
    """Check which runs should be retried, and retry them.

    It's safe to call this method on the same run multiple times because once a retry run is created,
    it won't create another. The only exception is if the new run gets deleted, in which case we'd
    retry the run again.
    """
    for run, retry_number in filter_runs_to_should_retry(
        [cast(DagsterRun, run_record.dagster_run) for run_record in run_records],
        workspace_process_context.instance,
        workspace_process_context.instance.run_retries_max_retries,
    ):
        yield

        try:
            retry_run(run, retry_number, workspace_process_context)
        except Exception:
            error_info = serializable_error_info_from_exc_info(sys.exc_info())
            workspace_process_context.instance.report_engine_event(
                "Failed to retry run",
                run,
                engine_event_data=EngineEventData(error=error_info),
            )
