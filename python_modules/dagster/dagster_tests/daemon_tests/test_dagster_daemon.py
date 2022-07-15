import pytest
from click.testing import CliRunner

from dagster._daemon.cli import run_command
from dagster._daemon.controller import daemon_controller_from_instance
from dagster._daemon.daemon import SchedulerDaemon
from dagster._daemon.run_coordinator.queued_run_coordinator_daemon import QueuedRunCoordinatorDaemon
from dagster.core.test_utils import instance_for_test
from dagster.core.workspace.load_target import EmptyWorkspaceTarget


def test_scheduler_instance():
    with instance_for_test(
        overrides={
            "scheduler": {
                "module": "dagster.core.scheduler",
                "class": "DagsterDaemonScheduler",
            },
        }
    ) as instance:
        with daemon_controller_from_instance(
            instance,
            workspace_load_target=EmptyWorkspaceTarget(),
        ) as controller:
            daemons = controller.daemons

            assert len(daemons) == 3

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
        with daemon_controller_from_instance(
            instance,
            workspace_load_target=EmptyWorkspaceTarget(),
        ) as controller:
            daemons = controller.daemons

            assert len(daemons) == 4
            assert any(isinstance(daemon, QueuedRunCoordinatorDaemon) for daemon in daemons)


def test_ephemeral_instance():
    runner = CliRunner()
    with pytest.raises(Exception, match="DAGSTER_HOME is not set"):
        runner.invoke(run_command, env={"DAGSTER_HOME": ""}, catch_exceptions=False)
