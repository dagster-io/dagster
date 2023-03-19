import logging
import os
import time
from logging import Logger
from typing import Any, Mapping, Optional, cast

import pendulum
import pytest
from dagster._core.events import DagsterEvent, DagsterEventType
from dagster._core.events.log import EventLogEntry
from dagster._core.instance import DagsterInstance
from dagster._core.launcher import CheckRunHealthResult, RunLauncher, WorkerStatus
from dagster._core.storage.pipeline_run import DagsterRunStatus
from dagster._core.storage.tags import MAX_RUNTIME_TAG
from dagster._core.test_utils import (
    create_run_for_test,
    create_test_daemon_workspace_context,
    environ,
    instance_for_test,
)
from dagster._core.workspace.context import WorkspaceProcessContext
from dagster._core.workspace.load_target import EmptyWorkspaceTarget
from dagster._daemon import get_default_daemon_logger
from dagster._daemon.monitoring.monitoring_daemon import monitor_started_run, monitor_starting_run
from dagster._serdes import ConfigurableClass
from dagster._serdes.config_class import ConfigurableClassData
from typing_extensions import Self


class TestRunLauncher(RunLauncher, ConfigurableClass):
    def __init__(self, inst_data: Optional[ConfigurableClassData] = None):
        self._inst_data = inst_data
        self.should_fail_termination = False
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
        return TestRunLauncher(inst_data=inst_data)

    def launch_run(self, context):
        self.launch_run_calls += 1

    def resume_run(self, context):
        self.resume_run_calls += 1

    def join(self, timeout=30):
        pass

    def terminate(self, run_id, message=None):
        self.termination_calls.append(run_id)
        if self.should_fail_termination:
            raise Exception("oof")

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
            "run_monitoring": {"enabled": True},
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
        pipeline_name=run.pipeline_name,
    )

    event_record = EventLogEntry(
        user_message="",
        level=logging.INFO,
        pipeline_name=run.pipeline_name,
        run_id=run.run_id,
        error_info=None,
        timestamp=timestamp,
        dagster_event=launch_started_event,
    )

    instance.handle_new_event(event_record)


def report_started_event(instance, run, timestamp):
    launch_started_event = DagsterEvent(
        event_type_value=DagsterEventType.PIPELINE_START.value,
        pipeline_name=run.pipeline_name,
    )

    event_record = EventLogEntry(
        user_message="",
        level=logging.INFO,
        pipeline_name=run.pipeline_name,
        run_id=run.run_id,
        error_info=None,
        timestamp=timestamp,
        dagster_event=launch_started_event,
    )

    instance.handle_new_event(event_record)


def test_monitor_starting(instance: DagsterInstance, logger: Logger):
    run = create_run_for_test(
        instance,
        pipeline_name="foo",
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

    run = create_run_for_test(instance, pipeline_name="foo")
    report_starting_event(instance, run, timestamp=time.time() - 1000)

    monitor_starting_run(
        instance,
        instance.get_run_record_by_id(run.run_id),  # type: ignore  # (possible none)
        logger,
    )
    run = instance.get_run_by_id(run.run_id)
    assert run
    assert run.status == DagsterRunStatus.FAILURE


def test_monitor_started(
    instance: DagsterInstance, workspace_context: WorkspaceProcessContext, logger: Logger
):
    run_id = create_run_for_test(
        instance, pipeline_name="foo", status=DagsterRunStatus.STARTED
    ).run_id
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
    initial = pendulum.now().subtract(1000)
    with pendulum.test(initial):
        too_long_run = create_run_for_test(
            instance,
            pipeline_name="foo",
            status=DagsterRunStatus.STARTING,
            tags={MAX_RUNTIME_TAG: "500"},
        )
        okay_run = create_run_for_test(
            instance,
            pipeline_name="foo",
            status=DagsterRunStatus.STARTING,
            tags={MAX_RUNTIME_TAG: "1000"},
        )
        run_no_tag = create_run_for_test(
            instance, pipeline_name="foo", status=DagsterRunStatus.STARTING
        )
    started_time = initial.add(seconds=1)
    with pendulum.test(started_time):
        report_started_event(instance, too_long_run, started_time.timestamp())
        report_started_event(instance, okay_run, started_time.timestamp())
        report_started_event(instance, run_no_tag, started_time.timestamp())

    too_long_record = instance.get_run_record_by_id(too_long_run.run_id)
    assert too_long_record is not None
    assert too_long_record.dagster_run.status == DagsterRunStatus.STARTED
    assert too_long_record.start_time == started_time.timestamp()

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

    eval_time = started_time.add(seconds=501)
    with pendulum.test(eval_time):
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


def test_long_running_termination_failure(
    instance: DagsterInstance, workspace_context: WorkspaceProcessContext, logger: Logger
):
    instance.run_launcher.should_fail_termination = True
    initial = pendulum.now().subtract(1000)
    with pendulum.test(initial):
        too_long_run = create_run_for_test(
            instance,
            pipeline_name="foo",
            status=DagsterRunStatus.STARTING,
            tags={MAX_RUNTIME_TAG: "500"},
        )
    started_time = initial.add(seconds=1)
    with pendulum.test(started_time):
        report_started_event(instance, too_long_run, started_time.timestamp())

    too_long_record = instance.get_run_record_by_id(too_long_run.run_id)
    assert too_long_record is not None
    assert too_long_record.dagster_run.status == DagsterRunStatus.STARTED
    assert too_long_record.start_time == started_time.timestamp()

    workspace = workspace_context.create_request_context()
    run_launcher = cast(TestRunLauncher, instance.run_launcher)

    eval_time = started_time.add(seconds=501)
    with pendulum.test(eval_time):
        # Enough runtime has elapsed for too_long_run to hit its maximum runtime so a
        # termination event should be triggered.
        monitor_started_run(instance, workspace, too_long_record, logger)
        run = instance.get_run_by_id(too_long_record.dagster_run.run_id)
        assert run
        assert run.status == DagsterRunStatus.CANCELED
        assert len(run_launcher.termination_calls) == 1
