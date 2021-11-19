# pylint: disable=redefined-outer-name

import logging
import os
import time

import pytest
from dagster.core.events import DagsterEvent, DagsterEventType
from dagster.core.events.log import EventLogEntry
from dagster.core.launcher import CheckRunHealthResult, RunLauncher, WorkerStatus
from dagster.core.storage.pipeline_run import PipelineRunStatus
from dagster.core.test_utils import (
    create_run_for_test,
    create_test_daemon_workspace,
    environ,
    instance_for_test,
)
from dagster.daemon import get_default_daemon_logger
from dagster.daemon.monitoring.monitoring_daemon import monitor_started_run, monitor_starting_run
from dagster.serdes import ConfigurableClass


class TestRunLauncher(RunLauncher, ConfigurableClass):
    def __init__(self, inst_data=None):
        self._inst_data = inst_data
        self.launch_run_calls = 0
        super().__init__()

    @property
    def inst_data(self):
        return self._inst_data

    @classmethod
    def config_type(cls):
        return {}

    @staticmethod
    def from_config_value(inst_data, config_value):
        return TestRunLauncher(inst_data=inst_data)

    def launch_run(self, context):
        self.launch_run_calls += 1

    def join(self, timeout=30):
        pass

    def can_terminate(self, run_id):
        raise NotImplementedError()

    def terminate(self, run_id):
        raise NotImplementedError()

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
def workspace():
    with create_test_daemon_workspace() as workspace:
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
        message="",
        user_message="",
        level=logging.INFO,
        pipeline_name=run.pipeline_name,
        run_id=run.run_id,
        error_info=None,
        timestamp=timestamp,
        dagster_event=launch_started_event,
    )

    instance.handle_new_event(event_record)


def test_monitor_starting(instance, logger):
    run = create_run_for_test(
        instance,
        pipeline_name="foo",
    )
    report_starting_event(instance, run, timestamp=time.time())
    monitor_starting_run(
        instance,
        instance.get_run_by_id(run.run_id),
        logger,
    )
    assert instance.get_run_by_id(run.run_id).status == PipelineRunStatus.STARTING

    run = create_run_for_test(instance, pipeline_name="foo")
    report_starting_event(instance, run, timestamp=time.time() - 1000)

    monitor_starting_run(
        instance,
        instance.get_run_by_id(run.run_id),
        logger,
    )
    assert instance.get_run_by_id(run.run_id).status == PipelineRunStatus.FAILURE


def test_monitor_started(instance, workspace, logger):

    run = create_run_for_test(instance, pipeline_name="foo", status=PipelineRunStatus.STARTED)
    with environ({"DAGSTER_TEST_RUN_HEALTH_CHECK_RESULT": "healthy"}):
        monitor_started_run(instance, workspace, run, logger)
        assert instance.get_run_by_id(run.run_id).status == PipelineRunStatus.STARTED
        assert instance.run_launcher.launch_run_calls == 0

    monitor_started_run(instance, workspace, run, logger)
    assert instance.get_run_by_id(run.run_id).status == PipelineRunStatus.STARTED
    assert instance.run_launcher.launch_run_calls == 1

    monitor_started_run(instance, workspace, run, logger)
    assert instance.get_run_by_id(run.run_id).status == PipelineRunStatus.STARTED
    assert instance.run_launcher.launch_run_calls == 2

    monitor_started_run(instance, workspace, run, logger)
    assert instance.get_run_by_id(run.run_id).status == PipelineRunStatus.STARTED
    assert instance.run_launcher.launch_run_calls == 3

    # exausted the 3 attempts
    monitor_started_run(instance, workspace, run, logger)
    assert instance.get_run_by_id(run.run_id).status == PipelineRunStatus.FAILURE
    assert instance.run_launcher.launch_run_calls == 3
