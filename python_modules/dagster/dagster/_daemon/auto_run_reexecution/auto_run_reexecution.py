import logging
import sys
from collections.abc import Iterator, Sequence
from typing import Optional, cast

import dagster._check as check
from dagster._core.definitions.metadata import MetadataValue
from dagster._core.definitions.selector import JobSubsetSelector
from dagster._core.errors import DagsterRunNotFoundError
from dagster._core.events import EngineEventData, RunFailureReason
from dagster._core.execution.plan.resume_retry import ReexecutionStrategy
from dagster._core.execution.retries import auto_reexecution_should_retry_run
from dagster._core.instance import DagsterInstance
from dagster._core.storage.dagster_run import DagsterRun, DagsterRunStatus, RunRecord
from dagster._core.storage.tags import (
    AUTO_RETRY_RUN_ID_TAG,
    RETRY_NUMBER_TAG,
    RETRY_ON_ASSET_OR_OP_FAILURE_TAG,
    RETRY_STRATEGY_TAG,
    RUN_FAILURE_REASON_TAG,
    WILL_RETRY_TAG,
)
from dagster._core.workspace.context import IWorkspaceProcessContext
from dagster._daemon.utils import DaemonErrorCapture
from dagster._utils.tags import get_boolean_tag_value

DEFAULT_REEXECUTION_POLICY = ReexecutionStrategy.FROM_FAILURE


def should_retry(run: DagsterRun, instance: DagsterInstance) -> bool:
    """A more robust method of determining is a run should be retried by the daemon than just looking
    at the WILL_RETRY_TAG. We account for the case where the code version is old and doesn't set the
    WILL_RETRY_TAG. If the tag wasn't set for a run failure, we set it so that other daemons can use the
    WILL_RETRY_TAG to determine if the run should be retried.
    """
    will_retry_tag_value = run.tags.get(WILL_RETRY_TAG)
    run_failure_reason = (
        RunFailureReason(run.tags.get(RUN_FAILURE_REASON_TAG))
        if run.tags.get(RUN_FAILURE_REASON_TAG)
        else None
    )
    if will_retry_tag_value is None:
        # If the run doesn't have the WILL_RETRY_TAG, and the run is failed, we
        # recalculate if the run should be retried to ensure backward compatibilty
        if run.status == DagsterRunStatus.FAILURE:
            should_retry_run = auto_reexecution_should_retry_run(instance, run, run_failure_reason)
            # add the tag to the run so that it can be used in other parts of the system
            instance.add_run_tags(run.run_id, {WILL_RETRY_TAG: str(should_retry_run).lower()})
        else:
            # run is not failed, and shouldn't be retried
            return False
    else:
        should_retry_run = get_boolean_tag_value(will_retry_tag_value, default_value=False)

    if should_retry_run:
        return should_retry_run
    else:
        # one of the reasons we may not retry a run is if it is a step failure and system is
        # set to not retry on op/asset failures. In this case, we log
        # an engine event
        retry_on_asset_or_op_failure = get_boolean_tag_value(
            run.tags.get(RETRY_ON_ASSET_OR_OP_FAILURE_TAG),
            default_value=instance.run_retries_retry_on_asset_or_op_failure,
        )
        if run_failure_reason == RunFailureReason.STEP_FAILURE and not retry_on_asset_or_op_failure:
            instance.report_engine_event(
                "Not retrying run since it failed due to an asset or op failure and run retries "
                "are configured with retry_on_asset_or_op_failure set to false.",
                run,
            )
        return False


def filter_runs_to_should_retry(
    runs: Sequence[DagsterRun], instance: DagsterInstance
) -> Iterator[DagsterRun]:
    """Return only runs that should retry along with their retry number (1st retry, 2nd, etc.)."""
    for run in runs:
        if should_retry(run, instance):
            yield run


def get_automatically_retried_run_if_exists(
    instance: DagsterInstance, run: DagsterRun, run_group: Sequence[DagsterRun]
) -> Optional[DagsterRun]:
    if run.tags.get(AUTO_RETRY_RUN_ID_TAG) is not None:
        return instance.get_run_by_id(run.tags[AUTO_RETRY_RUN_ID_TAG])
    child_run = next(
        (retried_run for retried_run in run_group if run.run_id == retried_run.parent_run_id), None
    )
    if child_run is not None and child_run.tags.get(RETRY_NUMBER_TAG) is not None:
        # We use the presense of RETRY_NUMBER_TAG to confirm that the child run was launched
        # by the automatic retry daemon. If the child run was launched by the user, the tag
        # should not be present.
        return child_run


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
    workspace_context: IWorkspaceProcessContext,
) -> None:
    """Submit a retry as a re-execute from failure."""
    instance = workspace_context.instance
    workspace = workspace_context.create_request_context()
    if not failed_run.remote_job_origin:
        instance.report_engine_event(
            "Run does not have an external job origin, unable to retry the run.",
            failed_run,
        )
        return

    origin = failed_run.remote_job_origin.repository_origin
    code_location = workspace.get_code_location(origin.code_location_origin.location_name)
    repo_name = origin.repository_name

    if not code_location.has_repository(repo_name):
        instance.report_engine_event(
            f"Could not find repository {repo_name} in location {code_location.name}, unable to"
            " retry the run. It was likely renamed or deleted.",
            failed_run,
        )
        return

    repo = code_location.get_repository(repo_name)

    if not repo.has_job(failed_run.job_name):
        instance.report_engine_event(
            f"Could not find job {failed_run.job_name} in repository {repo_name}, unable"
            " to retry the run. It was likely renamed or deleted.",
            failed_run,
        )
        return

    remote_job = code_location.get_job(
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

    try:
        _, run_group = check.not_none(instance.get_run_group(failed_run.run_id))
    except DagsterRunNotFoundError:
        instance.report_engine_event(
            f"Could not find run group for {failed_run.run_id}. This is most likely because the"
            " root run was deleted",
            failed_run,
        )
        return

    run_group_list = list(run_group)

    # it is possible for the daemon to die between creating the run and submitting it. We account for this
    # possibility by checking if the a run already exists in the run group with the parent run id of the
    # failed run and resubmit it if necessary.
    existing_retried_run = get_automatically_retried_run_if_exists(
        instance=instance, run=failed_run, run_group=run_group_list
    )
    if existing_retried_run is not None:
        # ensure the failed_run has the AUTO_RETRY_RUN_ID_TAG set
        if failed_run.tags.get(AUTO_RETRY_RUN_ID_TAG) is None:
            instance.add_run_tags(
                failed_run.run_id, {AUTO_RETRY_RUN_ID_TAG: existing_retried_run.run_id}
            )
        if existing_retried_run.status == DagsterRunStatus.NOT_STARTED:
            # A run already exists but was not submitted.
            instance.submit_run(existing_retried_run.run_id, workspace)
        return

    # At this point we know we need to launch a new run for the retry
    strategy = get_reexecution_strategy(failed_run, instance) or DEFAULT_REEXECUTION_POLICY
    tags = {RETRY_NUMBER_TAG: str(len(run_group_list))}
    new_run = instance.create_reexecuted_run(
        parent_run=failed_run,
        code_location=code_location,
        remote_job=remote_job,
        strategy=strategy,
        extra_tags=tags,
        use_parent_run_tags=True,
    )
    instance.add_run_tags(failed_run.run_id, {AUTO_RETRY_RUN_ID_TAG: new_run.run_id})

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
    logger: logging.Logger,
) -> Iterator[None]:
    """Check which runs should be retried, and retry them.

    It's safe to call this method on the same run multiple times because once a retry run is created,
    it won't create another. The only exception is if the new run gets deleted, in which case we'd
    retry the run again.
    """
    for run in filter_runs_to_should_retry(
        [cast(DagsterRun, run_record.dagster_run) for run_record in run_records],
        workspace_process_context.instance,
    ):
        yield
        try:
            retry_run(run, workspace_process_context)
        except Exception:
            error_info = DaemonErrorCapture.process_exception(
                exc_info=sys.exc_info(),
                logger=logger,
                log_message=f"Failed to retry run {run.run_id}",
            )
            workspace_process_context.instance.report_engine_event(
                "Failed to retry run",
                run,
                engine_event_data=EngineEventData(error=error_info),
            )
            # Since something failed when retrying this run, mark that we will not retry it so that we
            # don't retry it again in the future, and so that the tags reflect the state of the system.
            # We may want to split out the kinds of exceptions and handle them differently in the future so
            # that this can be more resiliant to transient errors. However, this would also require some changes
            # to the EventLogConsumerDaemon so that the cursors are not updated in a way that prevents this run
            # from being processed in the next tick.
            workspace_process_context.instance.add_run_tags(
                run_id=run.run_id, new_tags={WILL_RETRY_TAG: "false"}
            )
