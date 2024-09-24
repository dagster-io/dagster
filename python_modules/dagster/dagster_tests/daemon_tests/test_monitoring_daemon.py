import datetime
import logging
import os
import time
from logging import Logger
from typing import Any, Mapping, Optional, cast

import dagster._check as check
import pytest
from dagster._core.events import DagsterEvent, DagsterEventType, RunFailureReason
from dagster._core.events.log import EventLogEntry
from dagster._core.instance import DagsterInstance
from dagster._core.launcher import CheckRunHealthResult, RunLauncher, WorkerStatus
from dagster._core.storage.dagster_run import DagsterRun, DagsterRunStatus
from dagster._core.storage.tags import MAX_RUNTIME_SECONDS_TAG, RUN_FAILURE_REASON_TAG
from dagster._core.test_utils import (
    create_run_for_test,
    create_test_daemon_workspace_context,
    environ,
    freeze_time,
    instance_for_test,
)
from dagster._core.workspace.context import WorkspaceProcessContext
from dagster._core.workspace.load_target import EmptyWorkspaceTarget
from dagster._daemon import get_default_daemon_logger
from dagster._daemon.monitoring.run_monitoring import (
    monitor_canceling_run,
    monitor_started_run,
    monitor_starting_run,
)
from dagster._serdes import ConfigurableClass
from dagster._serdes.config_class import ConfigurableClassData
from dagster._time import create_datetime
from typing_extensions import Self


class TestRunLauncher(RunLauncher, ConfigurableClass):
    def __init__(self, inst_data: Optional[ConfigurableClassData] = None):
        self._inst_data = inst_data
        self.should_fail_termination = False
        self.should_except_termination = False
        self.launch_run_calls = 0
        self.resume_run_calls = 0
        self.termination_calls = []
        super().__init__()

    @property
    def inst_data(self):
        return self._inst_data

    @classmethod
    def config_type(cls):
        return {}

    @classmethod
    def from_config_value(
        cls, inst_data: ConfigurableClassData, config_value: Mapping[str, Any]
    ) -> Self:
        return cls(inst_data=inst_data)

    def launch_run(self, context):
        self.launch_run_calls += 1

    def resume_run(self, context):
        self.resume_run_calls += 1

    def join(self, timeout=30):
        pass

    def terminate(self, run_id):
        self.termination_calls.append(run_id)
        if self.should_fail_termination:
            return False
        if self.should_except_termination:
            raise Exception("oof")
        return True

    @property
    def supports_resume_run(self):
        return True

    @property
    def supports_check_run_worker_health(self):
        return True

    def check_run_worker_health(self, _run):
        return (
            CheckRunHealthResult(WorkerStatus.RUNNING, "")
            if os.environ.get("DAGSTER_TEST_RUN_HEALTH_CHECK_RESULT") == "healthy"
            else CheckRunHealthResult(WorkerStatus.NOT_FOUND, "")
        )


@pytest.fixture
def instance():
    with instance_for_test(
        overrides={
            "run_launcher": {
                "module": "dagster_tests.daemon_tests.test_monitoring_daemon",
                "class": "TestRunLauncher",
            },
            "run_monitoring": {
                "enabled": True,
                "max_resume_run_attempts": 3,
                "max_runtime_seconds": 750,
            },
        },
    ) as instance:
        yield instance


@pytest.fixture
def workspace_context(instance):
    with create_test_daemon_workspace_context(
        workspace_load_target=EmptyWorkspaceTarget(), instance=instance
    ) as workspace:
        yield workspace


@pytest.fixture
def logger():
    return get_default_daemon_logger("MonitoringDaemon")


def report_starting_event(instance, run, timestamp):
    launch_started_event = DagsterEvent(
        event_type_value=DagsterEventType.PIPELINE_STARTING.value,
        job_name=run.job_name,
    )

    event_record = EventLogEntry(
        user_message="",
        level=logging.INFO,
        job_name=run.job_name,
        run_id=run.run_id,
        error_info=None,
        timestamp=timestamp,
        dagster_event=launch_started_event,
    )

    instance.handle_new_event(event_record)


def report_started_event(instance: DagsterInstance, run: DagsterRun, timestamp: float) -> None:
    launch_started_event = DagsterEvent(
        event_type_value=DagsterEventType.PIPELINE_START.value,
        job_name=run.job_name,
    )

    event_record = EventLogEntry(
        user_message="",
        level=logging.INFO,
        job_name=run.job_name,
        run_id=run.run_id,
        error_info=None,
        timestamp=timestamp,
        dagster_event=launch_started_event,
    )

    instance.handle_new_event(event_record)


def report_canceling_event(instance, run, timestamp):
    launch_started_event = DagsterEvent(
        event_type_value=DagsterEventType.PIPELINE_CANCELING.value,
        job_name=run.job_name,
    )

    event_record = EventLogEntry(
        user_message="",
        level=logging.INFO,
        job_name=run.job_name,
        run_id=run.run_id,
        error_info=None,
        timestamp=timestamp,
        dagster_event=launch_started_event,
    )

    instance.handle_new_event(event_record)


def test_monitor_starting(instance: DagsterInstance, logger: Logger):
    run = create_run_for_test(
        instance,
        job_name="foo",
    )
    report_starting_event(instance, run, timestamp=time.time())
    monitor_starting_run(
        instance,
        instance.get_run_record_by_id(run.run_id),  # type: ignore  # (possible none)
        logger,
    )
    run = instance.get_run_by_id(run.run_id)
    assert run
    assert run.status == DagsterRunStatus.STARTING

    run = create_run_for_test(instance, job_name="foo")
    report_starting_event(instance, run, timestamp=time.time() - 1000)

    monitor_starting_run(
        instance,
        check.not_none(instance.get_run_record_by_id(run.run_id)),
        logger,
    )
    run = instance.get_run_by_id(run.run_id)
    assert run
    assert run.status == DagsterRunStatus.FAILURE
    assert run.tags[RUN_FAILURE_REASON_TAG] == RunFailureReason.START_TIMEOUT.value


def test_monitor_canceling(instance: DagsterInstance, logger: Logger):
    run = create_run_for_test(
        instance,
        job_name="foo",
    )

    now = time.time()

    report_starting_event(instance, run, timestamp=now)
    report_canceling_event(instance, run, timestamp=now + 1)

    monitor_canceling_run(
        instance,
        check.not_none(instance.get_run_record_by_id(run.run_id)),
        logger,
    )
    run = instance.get_run_by_id(run.run_id)
    assert run
    assert run.status == DagsterRunStatus.CANCELING

    run = create_run_for_test(instance, job_name="foo")
    report_canceling_event(instance, run, timestamp=now - 1000)

    monitor_canceling_run(
        instance,
        check.not_none(instance.get_run_record_by_id(run.run_id)),
        logger,
    )
    run = instance.get_run_by_id(run.run_id)
    assert run
    assert run.status == DagsterRunStatus.CANCELED


def test_monitor_started(
    instance: DagsterInstance, workspace_context: WorkspaceProcessContext, logger: Logger
):
    run_id = create_run_for_test(instance, job_name="foo", status=DagsterRunStatus.STARTED).run_id
    run_record = instance.get_run_record_by_id(run_id)
    assert run_record is not None
    workspace = workspace_context.create_request_context()
    run_launcher = cast(TestRunLauncher, instance.run_launcher)
    with environ({"DAGSTER_TEST_RUN_HEALTH_CHECK_RESULT": "healthy"}):
        monitor_started_run(instance, workspace, run_record, logger)
        run = instance.get_run_by_id(run_record.dagster_run.run_id)
        assert run
        assert run.status == DagsterRunStatus.STARTED
        assert run_launcher.launch_run_calls == 0
        assert run_launcher.resume_run_calls == 0

    monitor_started_run(instance, workspace, run_record, logger)
    run = instance.get_run_by_id(run.run_id)
    assert run
    assert run.status == DagsterRunStatus.STARTED
    assert run_launcher.launch_run_calls == 0
    assert run_launcher.resume_run_calls == 1

    monitor_started_run(instance, workspace, run_record, logger)
    run = instance.get_run_by_id(run.run_id)
    assert run
    assert run.status == DagsterRunStatus.STARTED
    assert run_launcher.launch_run_calls == 0
    assert run_launcher.resume_run_calls == 2

    monitor_started_run(instance, workspace, run_record, logger)
    run = instance.get_run_by_id(run.run_id)
    assert run
    assert run.status == DagsterRunStatus.STARTED
    assert run_launcher.launch_run_calls == 0
    assert run_launcher.resume_run_calls == 3

    # exausted the 3 attempts
    monitor_started_run(instance, workspace, run_record, logger)
    run = instance.get_run_by_id(run.run_id)
    assert run
    assert run.status == DagsterRunStatus.FAILURE
    assert run_launcher.launch_run_calls == 0
    assert run_launcher.resume_run_calls == 3


def test_long_running_termination(
    instance: DagsterInstance, workspace_context: WorkspaceProcessContext, logger: Logger
):
    with environ({"DAGSTER_TEST_RUN_HEALTH_CHECK_RESULT": "healthy"}):
        initial = create_datetime(2021, 1, 1)
        with freeze_time(initial):
            too_long_run = create_run_for_test(
                instance,
                job_name="foo",
                status=DagsterRunStatus.STARTING,
                tags={MAX_RUNTIME_SECONDS_TAG: "500"},
            )
            too_long_run_other_tag_value = create_run_for_test(
                instance,
                job_name="foo",
                status=DagsterRunStatus.STARTING,
                tags={"dagster/max_runtime_seconds": "500"},
            )
            okay_run = create_run_for_test(
                instance,
                job_name="foo",
                status=DagsterRunStatus.STARTING,
                tags={MAX_RUNTIME_SECONDS_TAG: "1000"},
            )
            run_no_tag = create_run_for_test(
                instance, job_name="foo", status=DagsterRunStatus.STARTING
            )
        started_time = initial + datetime.timedelta(seconds=1)
        with freeze_time(started_time):
            report_started_event(instance, too_long_run, started_time.timestamp())
            report_started_event(instance, too_long_run_other_tag_value, started_time.timestamp())
            report_started_event(instance, okay_run, started_time.timestamp())
            report_started_event(instance, run_no_tag, started_time.timestamp())

        too_long_record = instance.get_run_record_by_id(too_long_run.run_id)
        assert too_long_record is not None
        assert too_long_record.dagster_run.status == DagsterRunStatus.STARTED
        assert too_long_record.start_time == started_time.timestamp()

        too_long_other_tag_value_record = instance.get_run_record_by_id(
            too_long_run_other_tag_value.run_id
        )
        assert too_long_other_tag_value_record is not None
        assert too_long_other_tag_value_record.dagster_run.status == DagsterRunStatus.STARTED
        assert too_long_other_tag_value_record.start_time == started_time.timestamp()

        okay_record = instance.get_run_record_by_id(okay_run.run_id)
        assert okay_record is not None
        assert okay_record.dagster_run.status == DagsterRunStatus.STARTED
        assert okay_record.start_time == started_time.timestamp()

        no_tag_record = instance.get_run_record_by_id(run_no_tag.run_id)
        assert no_tag_record is not None
        assert no_tag_record.dagster_run.status == DagsterRunStatus.STARTED
        assert no_tag_record.start_time == started_time.timestamp()

        workspace = workspace_context.create_request_context()
        run_launcher = cast(TestRunLauncher, instance.run_launcher)

        eval_time = started_time + datetime.timedelta(seconds=501)
        with freeze_time(eval_time):
            # run_no_tag has no maximum run tag set, so no termination event should be
            # triggered.
            monitor_started_run(instance, workspace, no_tag_record, logger)
            run = instance.get_run_by_id(okay_record.dagster_run.run_id)
            assert run
            assert not run_launcher.termination_calls

            # Not enough time has elapsed for okay_run to hit its maximum runtime, so no
            # termination event should be triggered
            monitor_started_run(instance, workspace, okay_record, logger)
            run = instance.get_run_by_id(okay_record.dagster_run.run_id)
            assert run
            assert not run_launcher.termination_calls

            # Enough runtime has elapsed for too_long_run to hit its maximum runtime so a
            # termination event should be triggered.
            monitor_started_run(instance, workspace, too_long_record, logger)
            run = instance.get_run_by_id(too_long_record.dagster_run.run_id)
            assert run
            assert len(run_launcher.termination_calls) == 1
            run = instance.get_run_by_id(too_long_record.dagster_run.run_id)
            assert run
            assert run.status == DagsterRunStatus.FAILURE

            run_failure_events = instance.all_logs(
                too_long_record.dagster_run.run_id, of_type=DagsterEventType.RUN_FAILURE
            )
            assert len(run_failure_events) == 1
            event = run_failure_events[0].dagster_event
            assert event
            assert event.message == "Exceeded maximum runtime of 500 seconds."

            monitor_started_run(instance, workspace, too_long_other_tag_value_record, logger)
            run = instance.get_run_by_id(too_long_other_tag_value_record.dagster_run.run_id)
            assert run
            assert len(run_launcher.termination_calls) == 2
            run = instance.get_run_by_id(too_long_other_tag_value_record.dagster_run.run_id)
            assert run
            assert run.status == DagsterRunStatus.FAILURE

            run_failure_events = instance.all_logs(
                too_long_other_tag_value_record.dagster_run.run_id,
                of_type=DagsterEventType.RUN_FAILURE,
            )
            assert len(run_failure_events) == 1
            event = run_failure_events[0].dagster_event
            assert event
            assert event.message == "Exceeded maximum runtime of 500 seconds."

        # Wait long enough for the instance default to kick in
        eval_time = started_time + datetime.timedelta(seconds=751)
        with freeze_time(eval_time):
            # Still overridden to 1000 so no problem
            monitor_started_run(instance, workspace, okay_record, logger)
            run = instance.get_run_by_id(okay_record.dagster_run.run_id)
            assert run
            # no new termination calls
            assert len(run_launcher.termination_calls) == 2

            monitor_started_run(instance, workspace, no_tag_record, logger)
            run = instance.get_run_by_id(no_tag_record.dagster_run.run_id)
            assert run
            assert len(run_launcher.termination_calls) == 3
            run = instance.get_run_by_id(no_tag_record.dagster_run.run_id)
            assert run
            assert run.status == DagsterRunStatus.FAILURE


@pytest.mark.parametrize("failure_case", ["fail_termination", "termination_exception"])
def test_long_running_termination_failure(
    instance: DagsterInstance,
    workspace_context: WorkspaceProcessContext,
    logger: Logger,
    failure_case: str,
) -> None:
    with environ({"DAGSTER_TEST_RUN_HEALTH_CHECK_RESULT": "healthy"}):
        if failure_case == "fail_termination":
            instance.run_launcher.should_fail_termination = True  # type: ignore
        else:
            instance.run_launcher.should_except_termination = True  # type: ignore
        initial = create_datetime(2021, 1, 1)
        with freeze_time(initial):
            too_long_run = create_run_for_test(
                instance,
                job_name="foo",
                status=DagsterRunStatus.STARTING,
                tags={MAX_RUNTIME_SECONDS_TAG: "500"},
            )
        started_time = initial + datetime.timedelta(seconds=1)
        with freeze_time(started_time):
            report_started_event(instance, too_long_run, started_time.timestamp())

        too_long_record = instance.get_run_record_by_id(too_long_run.run_id)
        assert too_long_record is not None
        assert too_long_record.dagster_run.status == DagsterRunStatus.STARTED
        assert too_long_record.start_time == started_time.timestamp()

        workspace = workspace_context.create_request_context()
        run_launcher = cast(TestRunLauncher, instance.run_launcher)

        eval_time = started_time + datetime.timedelta(seconds=501)
        with freeze_time(eval_time):
            # Enough runtime has elapsed for too_long_run to hit its maximum runtime so a
            # termination event should be triggered.
            monitor_started_run(instance, workspace, too_long_record, logger)
            run = instance.get_run_by_id(too_long_record.dagster_run.run_id)
            assert run
            assert run.status == DagsterRunStatus.FAILURE
            assert len(run_launcher.termination_calls) == 1

        run_canceling_logs = instance.all_logs(run.run_id, of_type=DagsterEventType.RUN_CANCELING)
        assert len(run_canceling_logs) == 1
        run_canceling_log = run_canceling_logs[0]
        assert (
            run_canceling_log.message
            == "Canceling due to exceeding maximum runtime of 500 seconds."
        )

        run_failure_events = instance.all_logs(run.run_id, of_type=DagsterEventType.RUN_FAILURE)
        assert len(run_failure_events) == 1
        event = run_failure_events[0].dagster_event
        assert event
        assert (
            event.message == "This job is being forcibly marked as failed. The "
            "computational resources created by the run may not have been fully cleaned up."
        )
