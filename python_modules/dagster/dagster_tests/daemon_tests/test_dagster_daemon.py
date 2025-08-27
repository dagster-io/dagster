import json
from contextlib import contextmanager

import dagster as dg
import pytest
from click.testing import CliRunner
from dagster._core.workspace.load_target import EmptyWorkspaceTarget
from dagster._daemon.cli import run_command
from dagster._daemon.controller import daemon_controller_from_instance
from dagster._daemon.daemon import BackfillDaemon, SchedulerDaemon
from dagster._daemon.run_coordinator.queued_run_coordinator_daemon import QueuedRunCoordinatorDaemon
from dagster._utils.log import get_structlog_json_formatter


@pytest.mark.parametrize("daemon", ["backfills", "schedules", "sensors"])
def test_settings(daemon):
    settings = {"use_threads": True, "num_workers": 4}
    with dg.instance_for_test(overrides={daemon: settings}) as thread_inst:
        assert thread_inst.get_settings(daemon) == settings


@contextmanager
def daemon_from_instance(instance, daemon_type):
    with daemon_controller_from_instance(
        instance,
        workspace_load_target=EmptyWorkspaceTarget(),
    ) as controller:
        daemons = controller.daemons
        yield next(
            iter([daemon for daemon in daemons if daemon.daemon_type() == daemon_type]), None
        )


def test_scheduler_instance():
    with dg.instance_for_test(
        overrides={
            "scheduler": {
                "module": "dagster._core.scheduler",
                "class": "DagsterDaemonScheduler",
            },
        }
    ) as instance:
        with daemon_controller_from_instance(
            instance,
            workspace_load_target=EmptyWorkspaceTarget(),
        ) as controller:
            daemons = controller.daemons

            assert len(daemons) == 5

            assert any(isinstance(daemon, SchedulerDaemon) for daemon in daemons)


def test_run_coordinator_instance():
    with dg.instance_for_test(
        overrides={
            "run_coordinator": {
                "module": "dagster._core.run_coordinator.queued_run_coordinator",
                "class": "QueuedRunCoordinator",
            },
        }
    ) as instance:
        with daemon_controller_from_instance(
            instance,
            workspace_load_target=EmptyWorkspaceTarget(),
        ) as controller:
            daemons = controller.daemons

            assert len(daemons) == 5
            assert any(isinstance(daemon, QueuedRunCoordinatorDaemon) for daemon in daemons)


def test_ephemeral_instance():
    runner = CliRunner()
    with pytest.raises(Exception, match="DAGSTER_HOME is not set"):
        runner.invoke(run_command, env={"DAGSTER_HOME": ""}, catch_exceptions=False)


def test_daemon_json_logs(
    monkeypatch: pytest.MonkeyPatch,
    caplog: pytest.LogCaptureFixture,
) -> None:
    # https://github.com/pytest-dev/pytest/issues/2987#issuecomment-1460509126
    #
    # pytest captures log records using their handler. However, as a side-effect, this prevents
    # Dagster's log formatting from being applied in a unit test.
    #
    # To test the formatting, we monkeypatch the handler's formatter to use the same formatter as
    # the one used by Dagster when enabling JSON log format.
    monkeypatch.setattr(caplog.handler, "formatter", get_structlog_json_formatter())

    with (
        dg.instance_for_test() as instance,
        daemon_controller_from_instance(
            instance,
            workspace_load_target=EmptyWorkspaceTarget(),
            log_format="json",
        ),
    ):
        lines = [line for line in caplog.text.split("\n") if line]

        assert lines
        assert [json.loads(line) for line in lines]


def test_daemon_rich_logs() -> None:
    # Test that the daemon can be started with rich formatting.
    with dg.instance_for_test() as instance:
        daemon_controller_from_instance(
            instance,
            workspace_load_target=EmptyWorkspaceTarget(),
            log_format="rich",
        )


def test_backfill_threadpool():
    with dg.instance_for_test() as instance:
        with daemon_from_instance(instance, "BACKFILL") as backfill_daemon:
            assert isinstance(backfill_daemon, BackfillDaemon)
            assert backfill_daemon._threadpool_executor  # noqa: SLF001
            assert not backfill_daemon._submit_threadpool_executor  # noqa: SLF001

    with dg.instance_for_test(
        overrides={"backfills": {"use_threads": False, "num_workers": 4, "num_submit_workers": 4}}
    ) as instance:
        with daemon_from_instance(instance, "BACKFILL") as backfill_daemon:
            assert isinstance(backfill_daemon, BackfillDaemon)
            assert not backfill_daemon._threadpool_executor  # noqa: SLF001
            assert not backfill_daemon._submit_threadpool_executor  # noqa: SLF001

    with dg.instance_for_test(
        overrides={"backfills": {"use_threads": True, "num_workers": 4, "num_submit_workers": 4}}
    ) as instance:
        with daemon_from_instance(instance, "BACKFILL") as backfill_daemon:
            assert isinstance(backfill_daemon, BackfillDaemon)
            assert backfill_daemon._threadpool_executor  # noqa: SLF001
            assert backfill_daemon._submit_threadpool_executor  # noqa: SLF001

    with dg.instance_for_test(
        overrides={"backfills": {"num_workers": 4, "num_submit_workers": 4}}
    ) as instance:
        with daemon_from_instance(instance, "BACKFILL") as backfill_daemon:
            assert isinstance(backfill_daemon, BackfillDaemon)
            assert backfill_daemon._threadpool_executor  # noqa: SLF001
            assert backfill_daemon._submit_threadpool_executor  # noqa: SLF001

    with dg.instance_for_test(
        overrides={"backfills": {"use_threads": True, "num_workers": 4}}
    ) as instance:
        with daemon_from_instance(instance, "BACKFILL") as backfill_daemon:
            assert isinstance(backfill_daemon, BackfillDaemon)
            assert backfill_daemon._threadpool_executor  # noqa: SLF001
            assert not backfill_daemon._submit_threadpool_executor  # noqa: SLF001

    with dg.instance_for_test(
        overrides={"backfills": {"use_threads": True, "num_submit_workers": 4}}
    ) as instance:
        with daemon_from_instance(instance, "BACKFILL") as backfill_daemon:
            assert isinstance(backfill_daemon, BackfillDaemon)
            assert backfill_daemon._threadpool_executor  # noqa: SLF001
            assert backfill_daemon._submit_threadpool_executor  # noqa: SLF001
