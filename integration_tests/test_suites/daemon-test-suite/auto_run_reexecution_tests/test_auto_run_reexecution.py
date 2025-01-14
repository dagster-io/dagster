import logging
import time
from collections.abc import Sequence
from typing import cast
from unittest.mock import PropertyMock, patch

from dagster import DagsterEvent, DagsterEventType, DagsterInstance, EventLogEntry
from dagster._core.errors import DagsterUserCodeUnreachableError
from dagster._core.events import JobFailureData, RunFailureReason
from dagster._core.execution.api import create_execution_plan
from dagster._core.execution.plan.resume_retry import ReexecutionStrategy
from dagster._core.snap import snapshot_from_execution_plan
from dagster._core.storage.dagster_run import DagsterRun, DagsterRunStatus, RunsFilter
from dagster._core.storage.tags import (
    AUTO_RETRY_RUN_ID_TAG,
    MAX_RETRIES_TAG,
    PARENT_RUN_ID_TAG,
    RESUME_RETRY_TAG,
    RETRY_ON_ASSET_OR_OP_FAILURE_TAG,
    RETRY_STRATEGY_TAG,
    ROOT_RUN_ID_TAG,
    WILL_RETRY_TAG,
)
from dagster._core.test_utils import MockedRunCoordinator, create_run_for_test, instance_for_test
from dagster._daemon.auto_run_reexecution.auto_run_reexecution import (
    consume_new_runs_for_automatic_reexecution,
    filter_runs_to_should_retry,
    get_reexecution_strategy,
)
from dagster._daemon.auto_run_reexecution.event_log_consumer import EventLogConsumerDaemon

from auto_run_reexecution_tests.utils import foo, get_foo_job_handle

logger = logging.getLogger("dagster.test_auto_run_reexecution")


def create_run(instance, **kwargs):
    with get_foo_job_handle(instance) as handle:
        execution_plan = create_execution_plan(
            foo, step_keys_to_execute=kwargs.get("step_keys_to_execute")
        )
        return create_run_for_test(
            instance,
            remote_job_origin=handle.get_remote_origin(),
            job_code_origin=handle.get_python_origin(),
            job_name=handle.job_name,
            job_snapshot=foo.get_job_snapshot(),
            execution_plan_snapshot=snapshot_from_execution_plan(
                execution_plan, foo.get_job_snapshot_id()
            ),
            **kwargs,
        )


def process_runs_in_queue(instance, queue: Sequence[DagsterRun]):
    """The MockedRunCoordinator doesn't update the status of a run when submit_run is called. All other
    RunCoordinators move the run from NOT_STARTED to another status, so post-process the queue to update the
    status of each run to QUEUED, since the auto-reexecution logic checks the status of the runs.
    """
    for run in queue:
        updated_run = instance.get_run_by_id(run.run_id)
        if updated_run.status == DagsterRunStatus.NOT_STARTED:
            launch_started_event = DagsterEvent(
                event_type_value=DagsterEventType.PIPELINE_STARTING.value,
                job_name=run.job_name,
            )
            instance.report_dagster_event(launch_started_event, run_id=run.run_id)


def test_filter_runs_to_should_retry(instance):
    max_retries_setting = 2
    instance.wipe()
    with patch(
        instance.__class__.__module__
        + "."
        + instance.__class__.__name__
        + ".run_retries_max_retries",
        new_callable=PropertyMock,
    ) as mock_max_run_retries:
        mock_max_run_retries.return_value = max_retries_setting

        run = create_run(instance, status=DagsterRunStatus.STARTED)

        assert list(filter_runs_to_should_retry([run], instance)) == []

        dagster_event = DagsterEvent(
            event_type_value=DagsterEventType.PIPELINE_FAILURE.value,
            job_name="foo",
            message="",
        )
        event_record = EventLogEntry(
            user_message="",
            level=logging.ERROR,
            job_name="foo",
            run_id=run.run_id,
            error_info=None,
            timestamp=time.time(),
            dagster_event=dagster_event,
        )
        instance.handle_new_event(event_record)
        run = instance.get_run_by_id(run.run_id)
        assert run
        assert run.tags.get(WILL_RETRY_TAG) == "true"

        assert (
            len(
                list(
                    filter_runs_to_should_retry(
                        instance.get_runs(filters=RunsFilter(statuses=[DagsterRunStatus.FAILURE])),
                        instance,
                    )
                )
            )
            == 1
        )


def test_filter_runs_no_retry_on_asset_or_op_failure(instance_no_retry_on_asset_or_op_failure):
    max_retries_setting = 2
    instance = instance_no_retry_on_asset_or_op_failure
    with patch(
        instance.__class__.__module__
        + "."
        + instance.__class__.__name__
        + ".run_retries_max_retries",
        new_callable=PropertyMock,
    ) as mock_max_run_retries:
        mock_max_run_retries.return_value = max_retries_setting

        run = create_run(instance, status=DagsterRunStatus.STARTED, tags={MAX_RETRIES_TAG: "2"})

        assert list(filter_runs_to_should_retry([run], instance)) == []

        dagster_event = DagsterEvent(
            event_type_value=DagsterEventType.PIPELINE_FAILURE.value,
            job_name=run.job_name,
            message="oops step failure",
            event_specific_data=JobFailureData(
                error=None, failure_reason=RunFailureReason.STEP_FAILURE
            ),
        )
        instance.report_dagster_event(dagster_event, run_id=run.run_id, log_level=logging.ERROR)
        run = instance.get_run_by_id(run.run_id)
        assert run
        assert run.tags.get(WILL_RETRY_TAG) == "false"

        # doesn't retry because its a step failure
        assert (
            len(
                list(
                    filter_runs_to_should_retry(
                        instance.get_runs(filters=RunsFilter(statuses=[DagsterRunStatus.FAILURE])),
                        instance,
                    )
                )
            )
            == 0
        )

        assert any(
            "Not retrying run since it failed due to an asset or op failure and run retries are configured with retry_on_asset_or_op_failure set to false."
            in str(event)
            for event in instance.all_logs(run.run_id)
        )

        run = create_run(
            instance,
            status=DagsterRunStatus.STARTED,
            tags={MAX_RETRIES_TAG: "2", RETRY_ON_ASSET_OR_OP_FAILURE_TAG: False},
        )

        dagster_event = DagsterEvent(
            event_type_value=DagsterEventType.PIPELINE_FAILURE.value,
            job_name=run.job_name,
            message="oops step failure",
            event_specific_data=JobFailureData(
                error=None, failure_reason=RunFailureReason.STEP_FAILURE
            ),
        )
        instance.report_dagster_event(dagster_event, run_id=run.run_id, log_level=logging.ERROR)
        run = instance.get_run_by_id(run.run_id)
        assert run
        assert run.tags.get(WILL_RETRY_TAG) == "false"

        # does not retry due to the RETRY_ON_ASSET_OR_OP_FAILURE_TAG tag being false
        assert (
            len(
                list(
                    filter_runs_to_should_retry(
                        instance.get_runs(filters=RunsFilter(statuses=[DagsterRunStatus.FAILURE])),
                        instance,
                    )
                )
            )
            == 0
        )

        run = create_run(
            instance,
            status=DagsterRunStatus.STARTED,
            tags={MAX_RETRIES_TAG: "2", RETRY_ON_ASSET_OR_OP_FAILURE_TAG: True},
        )

        dagster_event = DagsterEvent(
            event_type_value=DagsterEventType.PIPELINE_FAILURE.value,
            job_name=run.job_name,
            message="oops step failure",
            event_specific_data=JobFailureData(
                error=None, failure_reason=RunFailureReason.STEP_FAILURE
            ),
        )
        instance.report_dagster_event(dagster_event, run_id=run.run_id, log_level=logging.ERROR)
        run = instance.get_run_by_id(run.run_id)
        assert run
        assert run.tags.get(WILL_RETRY_TAG) == "true"

        # does retry due to the RETRY_ON_ASSET_OR_OP_FAILURE_TAG tag being true
        runs_to_retry = list(
            filter_runs_to_should_retry(
                instance.get_runs(filters=RunsFilter(statuses=[DagsterRunStatus.FAILURE])),
                instance,
            )
        )
        assert len(runs_to_retry) == 1


def test_filter_runs_to_should_retry_tags(instance):
    instance.wipe()
    max_retries_setting = 2
    with patch(
        instance.__class__.__module__
        + "."
        + instance.__class__.__name__
        + ".run_retries_max_retries",
        new_callable=PropertyMock,
    ) as mock_max_run_retries:
        mock_max_run_retries.return_value = max_retries_setting

        run = create_run(instance, status=DagsterRunStatus.STARTED, tags={MAX_RETRIES_TAG: "0"})

        assert list(filter_runs_to_should_retry([run], instance)) == []

        instance.report_run_failed(run)
        run = instance.get_run_by_id(run.run_id)
        assert run
        assert run.tags.get(WILL_RETRY_TAG) == "false"

        assert (
            len(
                list(
                    filter_runs_to_should_retry(
                        instance.get_runs(filters=RunsFilter(statuses=[DagsterRunStatus.FAILURE])),
                        instance,
                    )
                )
            )
            == 0
        )

    instance.wipe()
    max_retries_setting = 0
    with patch(
        instance.__class__.__module__
        + "."
        + instance.__class__.__name__
        + ".run_retries_max_retries",
        new_callable=PropertyMock,
    ) as mock_max_run_retries:
        mock_max_run_retries.return_value = max_retries_setting

        run = create_run(instance, status=DagsterRunStatus.STARTED, tags={MAX_RETRIES_TAG: "10"})

        assert list(filter_runs_to_should_retry([run], instance)) == []

        instance.report_run_failed(run)
        run = instance.get_run_by_id(run.run_id)
        assert run
        assert run.tags.get(WILL_RETRY_TAG) == "true"

        assert (
            len(
                list(
                    filter_runs_to_should_retry(
                        instance.get_runs(filters=RunsFilter(statuses=[DagsterRunStatus.FAILURE])),
                        instance,
                    )
                )
            )
            == 1
        )

    instance.wipe()
    max_retries_setting = 2
    with patch(
        instance.__class__.__module__
        + "."
        + instance.__class__.__name__
        + ".run_retries_max_retries",
        new_callable=PropertyMock,
    ) as mock_max_run_retries:
        mock_max_run_retries.return_value = max_retries_setting

        run = create_run(
            instance, status=DagsterRunStatus.STARTED, tags={MAX_RETRIES_TAG: "not-an-int"}
        )

        assert list(filter_runs_to_should_retry([run], instance)) == []

        instance.report_run_failed(run)
        run = instance.get_run_by_id(run.run_id)
        assert run
        assert run.tags.get(WILL_RETRY_TAG) == "false"

        assert (
            list(
                filter_runs_to_should_retry(
                    instance.get_runs(filters=RunsFilter(statuses=[DagsterRunStatus.FAILURE])),
                    instance,
                )
            )
            == []
        )


def test_fallback_to_computing_should_retry_if_tag_not_present(instance):
    max_retries_setting = 2
    instance.wipe()
    with patch(
        instance.__class__.__module__
        + "."
        + instance.__class__.__name__
        + ".run_retries_max_retries",
        new_callable=PropertyMock,
    ) as mock_max_run_retries:
        mock_max_run_retries.return_value = max_retries_setting
        with patch(
            instance.__class__.__module__
            + "."
            + instance.__class__.__name__
            + ".run_retries_enabled",
            new_callable=PropertyMock,
        ) as mock_run_retries_enabled:
            # mock the return of run_retries_enabled to False so that the WILL_RETRY tag is not set on
            # the run
            mock_run_retries_enabled.return_value = False

            run = create_run(instance, status=DagsterRunStatus.STARTED)

            assert list(filter_runs_to_should_retry([run], instance)) == []

            dagster_event = DagsterEvent(
                event_type_value=DagsterEventType.PIPELINE_FAILURE.value,
                job_name="foo",
                message="",
            )
            event_record = EventLogEntry(
                user_message="",
                level=logging.ERROR,
                job_name="foo",
                run_id=run.run_id,
                error_info=None,
                timestamp=time.time(),
                dagster_event=dagster_event,
            )
            instance.handle_new_event(event_record)
            run = instance.get_run_by_id(run.run_id)
            assert run
            assert run.tags.get(WILL_RETRY_TAG) is None

        # filter_runs_to_should_retry should see that the WILL_RETRY tag is not set and recompute
        # if the run should be retried. It will also add the tag
        assert (
            len(
                list(
                    filter_runs_to_should_retry(
                        instance.get_runs(filters=RunsFilter(statuses=[DagsterRunStatus.FAILURE])),
                        instance,
                    )
                )
            )
            == 1
        )

        run = instance.get_run_by_id(run.run_id)
        assert run
        assert run.tags.get(WILL_RETRY_TAG) == "true"


def test_consume_new_runs_for_automatic_reexecution(instance, workspace_context):
    instance.wipe()
    instance.run_coordinator.queue().clear()
    list(
        consume_new_runs_for_automatic_reexecution(
            workspace_context,
            instance.get_run_records(filters=RunsFilter(statuses=[DagsterRunStatus.FAILURE])),
            logger,
        )
    )

    assert len(instance.run_coordinator.queue()) == 0

    # retries failure
    run = create_run(
        instance,
        status=DagsterRunStatus.STARTED,
        tags={
            MAX_RETRIES_TAG: "2",
            RESUME_RETRY_TAG: "true",
            RETRY_STRATEGY_TAG: "ALL_STEPS",
        },
    )
    dagster_event = DagsterEvent(
        event_type_value=DagsterEventType.PIPELINE_FAILURE.value,
        job_name="foo",
        message="",
    )
    event_record = EventLogEntry(
        user_message="",
        level=logging.ERROR,
        job_name="foo",
        run_id=run.run_id,
        error_info=None,
        timestamp=time.time(),
        dagster_event=dagster_event,
    )
    instance.handle_new_event(event_record)
    run = instance.get_run_by_id(run.run_id)
    assert run
    assert run.tags.get(WILL_RETRY_TAG) == "true"

    list(
        consume_new_runs_for_automatic_reexecution(
            workspace_context,
            instance.get_run_records(filters=RunsFilter(statuses=[DagsterRunStatus.FAILURE])),
            logger,
        )
    )
    assert len(instance.run_coordinator.queue()) == 1
    process_runs_in_queue(instance, instance.run_coordinator.queue())
    first_retry = instance.get_run_by_id(instance.run_coordinator.queue()[0].run_id)
    run = instance.get_run_by_id(run.run_id)
    assert run.tags.get(AUTO_RETRY_RUN_ID_TAG) == first_retry.run_id

    # retry strategy is copied, "is_resume_retry" is not since the retry strategy is ALL_STEPS
    assert RESUME_RETRY_TAG not in first_retry.tags
    assert first_retry.tags.get(RETRY_STRATEGY_TAG) == "ALL_STEPS"

    # doesn't retry again
    list(
        consume_new_runs_for_automatic_reexecution(
            workspace_context,
            instance.get_run_records(filters=RunsFilter(statuses=[DagsterRunStatus.FAILURE])),
            logger,
        )
    )
    assert len(instance.run_coordinator.queue()) == 1

    # retries once the new run failed
    dagster_event = DagsterEvent(
        event_type_value=DagsterEventType.PIPELINE_FAILURE.value,
        job_name="foo",
        message="",
    )
    event_record = EventLogEntry(
        user_message="",
        level=logging.ERROR,
        job_name="foo",
        run_id=first_retry.run_id,
        error_info=None,
        timestamp=time.time(),
        dagster_event=dagster_event,
    )
    instance.handle_new_event(event_record)
    first_retry = instance.get_run_by_id(first_retry.run_id)
    assert first_retry
    assert first_retry.tags.get(WILL_RETRY_TAG) == "true"

    list(
        consume_new_runs_for_automatic_reexecution(
            workspace_context,
            instance.get_run_records(filters=RunsFilter(statuses=[DagsterRunStatus.FAILURE])),
            logger,
        )
    )
    assert len(instance.run_coordinator.queue()) == 2
    process_runs_in_queue(instance, instance.run_coordinator.queue())
    second_retry = instance.get_run_by_id(instance.run_coordinator.queue()[1].run_id)
    first_retry = instance.get_run_by_id(first_retry.run_id)
    assert first_retry.tags.get(AUTO_RETRY_RUN_ID_TAG) == second_retry.run_id

    # doesn't retry a third time
    dagster_event = DagsterEvent(
        event_type_value=DagsterEventType.PIPELINE_FAILURE.value,
        job_name="foo",
        message="",
    )
    event_record = EventLogEntry(
        user_message="",
        level=logging.ERROR,
        job_name="foo",
        run_id=second_retry.run_id,
        error_info=None,
        timestamp=time.time(),
        dagster_event=dagster_event,
    )
    instance.handle_new_event(event_record)
    second_retry = instance.get_run_by_id(second_retry.run_id)
    assert second_retry
    assert second_retry.tags.get(WILL_RETRY_TAG) == "false"

    list(
        consume_new_runs_for_automatic_reexecution(
            workspace_context,
            instance.get_run_records(filters=RunsFilter(statuses=[DagsterRunStatus.FAILURE])),
            logger,
        )
    )
    assert len(instance.run_coordinator.queue()) == 2
    second_retry = instance.get_run_by_id(second_retry.run_id)
    assert second_retry.tags.get(AUTO_RETRY_RUN_ID_TAG) is None


def test_consume_new_runs_for_automatic_reexecution_mimic_daemon_fails_before_run_is_launched(
    instance, workspace_context
):
    """Tests that the daemon can recover if it fails between creating the retry run
    (instance.create_reexecuted_run) and submitting the run (instance.submit_run). If the daemon fails
    between these two calls, the cursors will not be updated, and the original run will be processed again.
    This test asserts that the daemon is able to find the run that was created in the previous iteration
    and then submits it.
    """
    instance.wipe()
    instance.run_coordinator.queue().clear()
    list(
        consume_new_runs_for_automatic_reexecution(
            workspace_context,
            instance.get_run_records(filters=RunsFilter(statuses=[DagsterRunStatus.FAILURE])),
            logger,
        )
    )

    assert len(instance.run_coordinator.queue()) == 0

    run = create_run(instance, status=DagsterRunStatus.STARTED, tags={MAX_RETRIES_TAG: "2"})
    dagster_event = DagsterEvent(
        event_type_value=DagsterEventType.PIPELINE_FAILURE.value,
        job_name="foo",
        message="",
    )
    event_record = EventLogEntry(
        user_message="",
        level=logging.ERROR,
        job_name="foo",
        run_id=run.run_id,
        error_info=None,
        timestamp=time.time(),
        dagster_event=dagster_event,
    )
    instance.handle_new_event(event_record)
    run = instance.get_run_by_id(run.run_id)
    assert run
    assert run.tags.get(WILL_RETRY_TAG) == "true"

    list(
        consume_new_runs_for_automatic_reexecution(
            workspace_context,
            instance.get_run_records(filters=RunsFilter(statuses=[DagsterRunStatus.FAILURE])),
            logger,
        )
    )
    assert len(instance.run_coordinator.queue()) == 1
    first_retry_run_id = instance.run_coordinator.queue()[0].run_id

    # if the daemon fails between creating the run and submitting the run, the run will exist in the
    # db but not the run_coordinator queue
    instance.run_coordinator.queue().clear()
    assert len(instance.run_coordinator.queue()) == 0
    assert len(instance.get_runs()) == 2  # original run and retry run are both in the db
    assert instance.get_run_by_id(first_retry_run_id).status == DagsterRunStatus.NOT_STARTED

    list(
        consume_new_runs_for_automatic_reexecution(
            workspace_context,
            instance.get_run_records(filters=RunsFilter(statuses=[DagsterRunStatus.FAILURE])),
            logger,
        )
    )

    # because the retried run already exists, it is in the run group for the original run. Because
    # it is in the run group of the original run, we will see that the run group contains a run with
    # parent_run_id as the original run. Then the daemon will check that the run has been started and
    # submit the run if not. Since the first retried_run is not started, it will get resubmitted.
    assert len(instance.run_coordinator.queue()) == 1
    second_retry = instance.run_coordinator.queue()[0]
    run = instance.get_run_by_id(run.run_id)
    assert run.tags.get(AUTO_RETRY_RUN_ID_TAG) == second_retry.run_id
    # the second retry isn't a unique run, it's just a re-submission of the first run
    assert second_retry.run_id == first_retry_run_id


def test_consume_new_runs_for_automatic_reexecution_mimic_daemon_fails_before_retry_tag_is_added(
    instance, workspace_context
):
    instance.wipe()
    instance.run_coordinator.queue().clear()
    list(
        consume_new_runs_for_automatic_reexecution(
            workspace_context,
            instance.get_run_records(filters=RunsFilter(statuses=[DagsterRunStatus.FAILURE])),
            logger,
        )
    )

    assert len(instance.run_coordinator.queue()) == 0

    run = create_run(instance, status=DagsterRunStatus.STARTED, tags={MAX_RETRIES_TAG: "2"})
    dagster_event = DagsterEvent(
        event_type_value=DagsterEventType.PIPELINE_FAILURE.value,
        job_name="foo",
        message="",
    )
    event_record = EventLogEntry(
        user_message="",
        level=logging.ERROR,
        job_name="foo",
        run_id=run.run_id,
        error_info=None,
        timestamp=time.time(),
        dagster_event=dagster_event,
    )
    instance.handle_new_event(event_record)
    run = instance.get_run_by_id(run.run_id)
    assert run
    assert run.tags.get(WILL_RETRY_TAG) == "true"

    list(
        consume_new_runs_for_automatic_reexecution(
            workspace_context,
            instance.get_run_records(filters=RunsFilter(statuses=[DagsterRunStatus.FAILURE])),
            logger,
        )
    )
    assert len(instance.run_coordinator.queue()) == 1
    first_retry = instance.run_coordinator.queue()[0]

    # if the daemon fails between creating the run and adding the AUTO_RETRY_RUN_ID_TAG, the run will exist in the
    # db but not the run_coordinator queue
    instance.run_coordinator.queue().clear()
    assert len(instance.run_coordinator.queue()) == 0
    assert len(instance.get_runs()) == 2  # original run and retry run are both in the db
    # update the run to remove the AUTO_RETRY_RUN_ID_TAG to simulate the daemon failing before adding the tag
    run = instance.get_run_by_id(run.run_id)
    instance.delete_run(run.run_id)
    run_tags = run.tags
    del run_tags[AUTO_RETRY_RUN_ID_TAG]
    run = run.with_tags(run_tags)
    instance.add_run(run)

    assert len(instance.get_runs()) == 2  # original run and retry run are both in the db

    list(
        consume_new_runs_for_automatic_reexecution(
            workspace_context,
            instance.get_run_records(filters=RunsFilter(statuses=[DagsterRunStatus.FAILURE])),
            logger,
        )
    )

    # because the retried run already exists, it is in the run group for the original run. Because
    # it is in the run group of the original run, we will see that the run group contains a run with
    # parent_run_id as the original run. Then the daemon will check that the run has been started and
    # submit the run if not. Since the first retried_run is not started, it will get resubmitted.
    assert len(instance.run_coordinator.queue()) == 1
    second_retry = instance.run_coordinator.queue()[0]
    run = instance.get_run_by_id(run.run_id)
    assert run.tags.get(AUTO_RETRY_RUN_ID_TAG) == second_retry.run_id
    assert second_retry.run_id == first_retry.run_id


def test_consume_new_runs_for_automatic_reexecution_retry_run_deleted(instance, workspace_context):
    """This test documents the current behavior for the case when a retry run is deleted and the original
    run is processed by the retry daemon again. In this case, a new retry will be launched.

    Note that in practice, the original run would only be processed a second time if the daemon did not
    properly update its cursors.
    """
    instance.wipe()
    instance.run_coordinator.queue().clear()
    list(
        consume_new_runs_for_automatic_reexecution(
            workspace_context,
            instance.get_run_records(filters=RunsFilter(statuses=[DagsterRunStatus.FAILURE])),
            logger,
        )
    )

    assert len(instance.run_coordinator.queue()) == 0

    run = create_run(instance, status=DagsterRunStatus.STARTED, tags={MAX_RETRIES_TAG: "2"})
    dagster_event = DagsterEvent(
        event_type_value=DagsterEventType.PIPELINE_FAILURE.value,
        job_name="foo",
        message="",
    )
    event_record = EventLogEntry(
        user_message="",
        level=logging.ERROR,
        job_name="foo",
        run_id=run.run_id,
        error_info=None,
        timestamp=time.time(),
        dagster_event=dagster_event,
    )
    instance.handle_new_event(event_record)
    run = instance.get_run_by_id(run.run_id)
    assert run
    assert run.tags.get(WILL_RETRY_TAG) == "true"

    list(
        consume_new_runs_for_automatic_reexecution(
            workspace_context,
            instance.get_run_records(filters=RunsFilter(statuses=[DagsterRunStatus.FAILURE])),
            logger,
        )
    )
    assert len(instance.run_coordinator.queue()) == 1
    first_retry = instance.run_coordinator.queue()[0]
    run = instance.get_run_by_id(run.run_id)
    assert run.tags.get(AUTO_RETRY_RUN_ID_TAG) == first_retry.run_id

    # delete the run and remove it from the queue
    instance.delete_run(first_retry.run_id)
    instance.run_coordinator.queue().clear()
    assert len(instance.run_coordinator.queue()) == 0
    assert len(instance.get_runs()) == 1  # just the original run

    list(
        consume_new_runs_for_automatic_reexecution(
            workspace_context,
            instance.get_run_records(filters=RunsFilter(statuses=[DagsterRunStatus.FAILURE])),
            logger,
        )
    )

    assert len(instance.run_coordinator.queue()) == 1
    second_retry = instance.run_coordinator.queue()[0]
    run = instance.get_run_by_id(run.run_id)
    assert run.tags.get(AUTO_RETRY_RUN_ID_TAG) == second_retry.run_id


def test_code_location_unavailable(instance, workspace_context):
    """This test documents the behavior of the daemon if retry_run raises an exception. Since we
    catch any exception raised by retry_run and log the error instead of re-raising, the daemon will
    update the cursors and continue as normal. This means that if retry_run fails, the run will not
    get processed again by the daemon. So we need to mark that the run will not be retried so that
    the tags reflect the state of the system.

    If we modify the EventLogConsumerDaemon so that we can re-process runs where an error was raised, then
    we could reconsider this behavior and try to reprocess runs where something in retry_run failed.
    """
    instance.wipe()
    instance.run_coordinator.queue().clear()
    list(
        consume_new_runs_for_automatic_reexecution(
            workspace_context,
            instance.get_run_records(filters=RunsFilter(statuses=[DagsterRunStatus.FAILURE])),
            logger,
        )
    )

    assert len(instance.run_coordinator.queue()) == 0

    run = create_run(instance, status=DagsterRunStatus.STARTED, tags={MAX_RETRIES_TAG: "2"})
    dagster_event = DagsterEvent(
        event_type_value=DagsterEventType.PIPELINE_FAILURE.value,
        job_name="foo",
        message="",
    )
    event_record = EventLogEntry(
        user_message="",
        level=logging.ERROR,
        job_name="foo",
        run_id=run.run_id,
        error_info=None,
        timestamp=time.time(),
        dagster_event=dagster_event,
    )
    instance.handle_new_event(event_record)
    run = instance.get_run_by_id(run.run_id)
    assert run
    assert run.tags.get(WILL_RETRY_TAG) == "true"

    def raise_code_unreachable_error(*args, **kwargs):
        raise DagsterUserCodeUnreachableError()

    with patch(
        "dagster._daemon.auto_run_reexecution.auto_run_reexecution.retry_run",
        side_effect=raise_code_unreachable_error,
    ):
        list(
            consume_new_runs_for_automatic_reexecution(
                workspace_context,
                instance.get_run_records(filters=RunsFilter(statuses=[DagsterRunStatus.FAILURE])),
                logger,
            )
        )

        assert len(instance.run_coordinator.queue()) == 0
        run = instance.get_run_by_id(run.run_id)
        assert run
        assert run.tags.get(WILL_RETRY_TAG) == "false"


def test_consume_new_runs_for_automatic_reexecution_with_manual_retry(instance, workspace_context):
    """This test documents the current behavior for an edge case where a manual retry of a run is launched
    before the daemon processes the original run. In this case the daemon will not launch a retry of the
    original run because it sees a run in the run group with a parent_run_id of the original run.
    """
    instance.wipe()
    instance.run_coordinator.queue().clear()
    list(
        consume_new_runs_for_automatic_reexecution(
            workspace_context,
            instance.get_run_records(filters=RunsFilter(statuses=[DagsterRunStatus.FAILURE])),
            logger,
        )
    )

    assert len(instance.run_coordinator.queue()) == 0

    run = create_run(instance, status=DagsterRunStatus.STARTED, tags={MAX_RETRIES_TAG: "2"})
    dagster_event = DagsterEvent(
        event_type_value=DagsterEventType.PIPELINE_FAILURE.value,
        job_name="foo",
        message="",
    )
    event_record = EventLogEntry(
        user_message="",
        level=logging.ERROR,
        job_name="foo",
        run_id=run.run_id,
        error_info=None,
        timestamp=time.time(),
        dagster_event=dagster_event,
    )
    instance.handle_new_event(event_record)

    # before the auto-reexecution daemon can run, a user manually launches a retry
    manual_retry = create_run(
        instance,
        status=DagsterRunStatus.STARTED,
        parent_run_id=run.run_id,
        root_run_id=run.run_id,
        tags={MAX_RETRIES_TAG: "2", ROOT_RUN_ID_TAG: run.run_id, PARENT_RUN_ID_TAG: run.run_id},
    )

    list(
        consume_new_runs_for_automatic_reexecution(
            workspace_context,
            instance.get_run_records(filters=RunsFilter(statuses=[DagsterRunStatus.FAILURE])),
            logger,
        )
    )
    # the daemon can distinguish between a manual retry of a run and an auto-retry of a run and still
    # launch an automatic retry. Therefore the original run will be retried
    assert len(instance.run_coordinator.queue()) == 1
    retry_run = instance.run_coordinator.queue()[0]
    run = instance.get_run_by_id(run.run_id)
    assert run.tags.get(AUTO_RETRY_RUN_ID_TAG) == retry_run.run_id
    assert run.tags.get(AUTO_RETRY_RUN_ID_TAG) != manual_retry.run_id


def test_daemon_enabled(instance):
    with instance_for_test() as run_retries_disabled_instance:
        assert (
            EventLogConsumerDaemon.daemon_type()
            not in run_retries_disabled_instance.get_required_daemon_types()
        )

    assert EventLogConsumerDaemon.daemon_type() in instance.get_required_daemon_types()


def test_strategy(instance: DagsterInstance):
    run = create_run(
        instance,
        status=DagsterRunStatus.FAILURE,
    )
    assert get_reexecution_strategy(run, instance) is None

    run = create_run(
        instance,
        status=DagsterRunStatus.FAILURE,
        tags={RETRY_STRATEGY_TAG: "FROM_FAILURE"},
    )
    assert get_reexecution_strategy(run, instance) == ReexecutionStrategy.FROM_FAILURE

    run = create_run(
        instance,
        status=DagsterRunStatus.FAILURE,
        tags={RETRY_STRATEGY_TAG: "ALL_STEPS"},
    )
    assert get_reexecution_strategy(run, instance) == ReexecutionStrategy.ALL_STEPS

    run = create_run(
        instance,
        status=DagsterRunStatus.FAILURE,
        tags={RETRY_STRATEGY_TAG: "not a strategy"},
    )
    assert get_reexecution_strategy(run, instance) is None


def test_subset_run(instance: DagsterInstance, workspace_context):
    instance.wipe()
    run_coordinator = cast(MockedRunCoordinator, instance.run_coordinator)
    run_coordinator.queue().clear()

    # retries failure
    run = create_run(
        instance,
        status=DagsterRunStatus.STARTED,
        tags={MAX_RETRIES_TAG: "2"},
        op_selection=["do_something"],
        step_keys_to_execute=["do_something"],
    )

    dagster_event = DagsterEvent(
        event_type_value=DagsterEventType.PIPELINE_FAILURE.value,
        job_name="foo",
        message="",
    )
    event_record = EventLogEntry(
        user_message="",
        level=logging.ERROR,
        job_name="foo",
        run_id=run.run_id,
        error_info=None,
        timestamp=time.time(),
        dagster_event=dagster_event,
    )
    instance.handle_new_event(event_record)
    run = instance.get_run_by_id(run.run_id)
    assert run
    assert run.tags.get(WILL_RETRY_TAG) == "true"

    list(
        consume_new_runs_for_automatic_reexecution(
            workspace_context,
            instance.get_run_records(filters=RunsFilter(statuses=[DagsterRunStatus.FAILURE])),
            logger,
        )
    )
    assert len(run_coordinator.queue()) == 1
    auto_run = run_coordinator.queue()[0]
    assert auto_run.op_selection == ["do_something"]
    assert instance.get_execution_plan_snapshot(
        auto_run.execution_plan_snapshot_id
    ).step_keys_to_execute == ["do_something"]
    assert instance.get_job_snapshot(auto_run.job_snapshot_id).node_names == ["do_something"]
