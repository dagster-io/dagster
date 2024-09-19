import logging
import time
from typing import cast

from dagster import DagsterEvent, DagsterEventType, DagsterInstance, EventLogEntry
from dagster._core.events import JobFailureData, RunFailureReason
from dagster._core.execution.api import create_execution_plan
from dagster._core.execution.plan.resume_retry import ReexecutionStrategy
from dagster._core.snap import snapshot_from_execution_plan
from dagster._core.storage.dagster_run import DagsterRunStatus, RunsFilter
from dagster._core.storage.tags import (
    MAX_RETRIES_TAG,
    RETRY_ON_ASSET_OR_OP_FAILURE_TAG,
    RETRY_STRATEGY_TAG,
)
from dagster._core.test_utils import MockedRunCoordinator, create_run_for_test, instance_for_test
from dagster._daemon.auto_run_reexecution.auto_run_reexecution import (
    consume_new_runs_for_automatic_reexecution,
    filter_runs_to_should_retry,
    get_reexecution_strategy,
)
from dagster._daemon.auto_run_reexecution.event_log_consumer import EventLogConsumerDaemon

from auto_run_reexecution_tests.utils import foo, get_foo_job_handle


def create_run(instance, **kwargs):
    with get_foo_job_handle(instance) as handle:
        execution_plan = create_execution_plan(
            foo, step_keys_to_execute=kwargs.get("step_keys_to_execute")
        )
        return create_run_for_test(
            instance,
            external_job_origin=handle.get_external_origin(),
            job_code_origin=handle.get_python_origin(),
            job_name=handle.job_name,
            job_snapshot=foo.get_job_snapshot(),
            execution_plan_snapshot=snapshot_from_execution_plan(
                execution_plan, foo.get_job_snapshot_id()
            ),
            **kwargs,
        )


def test_filter_runs_to_should_retry(instance):
    instance.wipe()

    run = create_run(instance, status=DagsterRunStatus.STARTED)

    assert list(filter_runs_to_should_retry([run], instance, 2)) == []

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

    assert (
        len(
            list(
                filter_runs_to_should_retry(
                    instance.get_runs(filters=RunsFilter(statuses=[DagsterRunStatus.FAILURE])),
                    instance,
                    2,
                )
            )
        )
        == 1
    )


def test_filter_runs_no_retry_on_asset_or_op_failure(instance_no_retry_on_asset_or_op_failure):
    instance = instance_no_retry_on_asset_or_op_failure

    run = create_run(instance, status=DagsterRunStatus.STARTED, tags={MAX_RETRIES_TAG: "2"})

    assert list(filter_runs_to_should_retry([run], instance, 2)) == []

    dagster_event = DagsterEvent(
        event_type_value=DagsterEventType.PIPELINE_FAILURE.value,
        job_name=run.job_name,
        message="oops step failure",
        event_specific_data=JobFailureData(
            error=None, failure_reason=RunFailureReason.STEP_FAILURE
        ),
    )
    instance.report_dagster_event(dagster_event, run_id=run.run_id, log_level=logging.ERROR)

    # doesn't retry because its a step failure

    assert (
        len(
            list(
                filter_runs_to_should_retry(
                    instance.get_runs(filters=RunsFilter(statuses=[DagsterRunStatus.FAILURE])),
                    instance,
                    2,
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

    # does not retry due to the RETRY_ON_ASSET_OR_OP_FAILURE_TAG tag being false

    assert (
        len(
            list(
                filter_runs_to_should_retry(
                    instance.get_runs(filters=RunsFilter(statuses=[DagsterRunStatus.FAILURE])),
                    instance,
                    2,
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

    # does retry due to the RETRY_ON_ASSET_OR_OP_FAILURE_TAG tag being true

    assert (
        len(
            list(
                filter_runs_to_should_retry(
                    instance.get_runs(filters=RunsFilter(statuses=[DagsterRunStatus.FAILURE])),
                    instance,
                    2,
                )
            )
        )
        == 1
    )


def test_filter_runs_to_should_retry_tags(instance):
    instance.wipe()

    run = create_run(instance, status=DagsterRunStatus.STARTED, tags={MAX_RETRIES_TAG: "0"})

    assert list(filter_runs_to_should_retry([run], instance, 2)) == []

    instance.report_run_failed(run)

    assert (
        len(
            list(
                filter_runs_to_should_retry(
                    instance.get_runs(filters=RunsFilter(statuses=[DagsterRunStatus.FAILURE])),
                    instance,
                    2,
                )
            )
        )
        == 0
    )

    instance.wipe()

    run = create_run(instance, status=DagsterRunStatus.STARTED, tags={MAX_RETRIES_TAG: "10"})

    assert list(filter_runs_to_should_retry([run], instance, 0)) == []

    instance.report_run_failed(run)

    assert (
        len(
            list(
                filter_runs_to_should_retry(
                    instance.get_runs(filters=RunsFilter(statuses=[DagsterRunStatus.FAILURE])),
                    instance,
                    2,
                )
            )
        )
        == 1
    )

    instance.wipe()

    run = create_run(
        instance, status=DagsterRunStatus.STARTED, tags={MAX_RETRIES_TAG: "not-an-int"}
    )

    assert list(filter_runs_to_should_retry([run], instance, 0)) == []

    instance.report_run_failed(run)

    assert (
        list(
            filter_runs_to_should_retry(
                instance.get_runs(filters=RunsFilter(statuses=[DagsterRunStatus.FAILURE])),
                instance,
                2,
            )
        )
        == []
    )


def test_consume_new_runs_for_automatic_reexecution(instance, workspace_context):
    instance.wipe()
    instance.run_coordinator.queue().clear()

    list(
        consume_new_runs_for_automatic_reexecution(
            workspace_context,
            instance.get_run_records(filters=RunsFilter(statuses=[DagsterRunStatus.FAILURE])),
        )
    )

    assert len(instance.run_coordinator.queue()) == 0

    # retries failure
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

    list(
        consume_new_runs_for_automatic_reexecution(
            workspace_context,
            instance.get_run_records(filters=RunsFilter(statuses=[DagsterRunStatus.FAILURE])),
        )
    )
    assert len(instance.run_coordinator.queue()) == 1

    # doesn't retry again
    list(
        consume_new_runs_for_automatic_reexecution(
            workspace_context,
            instance.get_run_records(filters=RunsFilter(statuses=[DagsterRunStatus.FAILURE])),
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
        run_id=instance.run_coordinator.queue()[0].run_id,
        error_info=None,
        timestamp=time.time(),
        dagster_event=dagster_event,
    )
    instance.handle_new_event(event_record)
    list(
        consume_new_runs_for_automatic_reexecution(
            workspace_context,
            instance.get_run_records(filters=RunsFilter(statuses=[DagsterRunStatus.FAILURE])),
        )
    )
    assert len(instance.run_coordinator.queue()) == 2

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
        run_id=instance.run_coordinator.queue()[1].run_id,
        error_info=None,
        timestamp=time.time(),
        dagster_event=dagster_event,
    )
    instance.handle_new_event(event_record)
    list(
        consume_new_runs_for_automatic_reexecution(
            workspace_context,
            instance.get_run_records(filters=RunsFilter(statuses=[DagsterRunStatus.FAILURE])),
        )
    )
    assert len(instance.run_coordinator.queue()) == 2


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

    list(
        consume_new_runs_for_automatic_reexecution(
            workspace_context,
            instance.get_run_records(filters=RunsFilter(statuses=[DagsterRunStatus.FAILURE])),
        )
    )
    assert len(run_coordinator.queue()) == 1
    auto_run = run_coordinator.queue()[0]
    assert auto_run.op_selection == ["do_something"]
    assert instance.get_execution_plan_snapshot(
        auto_run.execution_plan_snapshot_id
    ).step_keys_to_execute == ["do_something"]
    assert instance.get_job_snapshot(auto_run.job_snapshot_id).node_names == ["do_something"]
