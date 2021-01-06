import datetime
import logging
import re

import pendulum
import pytest
from click.testing import CliRunner
from dagster.core.test_utils import instance_for_test
from dagster.daemon.cli import run_command
from dagster.daemon.controller import DagsterDaemonController
from dagster.daemon.daemon import SchedulerDaemon
from dagster.daemon.run_coordinator.queued_run_coordinator_daemon import QueuedRunCoordinatorDaemon
from dagster.daemon.types import DaemonType


def test_scheduler_instance():
    with instance_for_test(
        overrides={
            "scheduler": {"module": "dagster.core.scheduler", "class": "DagsterDaemonScheduler",},
        }
    ) as instance:
        controller = DagsterDaemonController(instance)

        daemons = controller.daemons

        assert len(daemons) == 2
        assert any(isinstance(daemon, SchedulerDaemon) for daemon in daemons)


def test_run_coordinator_instance():
    with instance_for_test(
        overrides={
            "run_coordinator": {
                "module": "dagster.core.run_coordinator.queued_run_coordinator",
                "class": "QueuedRunCoordinator",
            },
        }
    ) as instance:
        controller = DagsterDaemonController(instance)

        daemons = controller.daemons

        assert len(daemons) == 3
        assert any(isinstance(daemon, QueuedRunCoordinatorDaemon) for daemon in daemons)


def _scheduler_ran(caplog):
    for log_tuple in caplog.record_tuples:
        logger_name, _level, text = log_tuple

        if (
            logger_name == "SchedulerDaemon"
            and "Not checking for any runs since no schedules have been started." in text
        ):
            return True

    return False


def _run_coordinator_ran(caplog):
    for log_tuple in caplog.record_tuples:
        logger_name, _level, text = log_tuple

        if logger_name == "QueuedRunCoordinatorDaemon" and "Poll returned no queued runs." in text:
            return True

    return False


def test_ephemeral_instance():
    runner = CliRunner()
    with pytest.raises(
        Exception,
        match=re.escape(
            "dagster-daemon can't run using an in-memory instance. Make sure the DAGSTER_HOME environment variable has been set correctly and that you have created a dagster.yaml file there."
        ),
    ):
        runner.invoke(run_command, env={"DAGSTER_HOME": ""}, catch_exceptions=False)


def test_different_intervals(caplog):
    with instance_for_test(
        overrides={
            "scheduler": {"module": "dagster.core.scheduler", "class": "DagsterDaemonScheduler",},
            "run_coordinator": {
                "module": "dagster.core.run_coordinator.queued_run_coordinator",
                "class": "QueuedRunCoordinator",
                "config": {"dequeue_interval_seconds": 5},
            },
        }
    ) as instance:
        init_time = pendulum.now("UTC")
        controller = DagsterDaemonController(instance)

        assert caplog.record_tuples == [
            (
                "dagster-daemon",
                logging.INFO,
                "instance is configured with the following daemons: ['QueuedRunCoordinatorDaemon', 'SchedulerDaemon', 'SensorDaemon']",
            )
        ]

        controller.run_iteration(init_time)

        scheduler_daemon = controller.get_daemon(DaemonType.SCHEDULER)
        run_daemon = controller.get_daemon(DaemonType.QUEUED_RUN_COORDINATOR)

        assert scheduler_daemon
        assert (
            controller.get_daemon_last_iteration_time(scheduler_daemon.daemon_type()) == init_time
        )
        assert _scheduler_ran(caplog)

        assert run_daemon
        assert controller.get_daemon_last_iteration_time(run_daemon.daemon_type()) == init_time
        assert _run_coordinator_ran(caplog)
        caplog.clear()

        next_time = init_time + datetime.timedelta(seconds=5)
        controller.run_iteration(next_time)

        # Run coordinator does another iteration, scheduler does not
        assert (
            controller.get_daemon_last_iteration_time(scheduler_daemon.daemon_type()) == init_time
        )
        assert not _scheduler_ran(caplog)

        assert controller.get_daemon_last_iteration_time(run_daemon.daemon_type()) == next_time
        assert _run_coordinator_ran(caplog)
        caplog.clear()

        next_time = init_time + datetime.timedelta(seconds=30)
        controller.run_iteration(next_time)

        # 30 seconds later both daemons do another iteration
        assert (
            controller.get_daemon_last_iteration_time(scheduler_daemon.daemon_type()) == next_time
        )
        assert _scheduler_ran(caplog)

        assert controller.get_daemon_last_iteration_time(run_daemon.daemon_type()) == next_time
        assert _run_coordinator_ran(caplog)
