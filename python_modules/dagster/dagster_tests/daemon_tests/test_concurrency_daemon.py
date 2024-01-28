import tempfile
from logging import Logger

import pendulum
import pytest
from dagster._core.instance import DagsterInstance
from dagster._core.storage.dagster_run import DagsterRunStatus
from dagster._core.test_utils import (
    create_run_for_test,
    create_test_daemon_workspace_context,
    instance_for_test,
)
from dagster._core.workspace.context import WorkspaceProcessContext
from dagster._core.workspace.load_target import EmptyWorkspaceTarget
from dagster._daemon import get_default_daemon_logger
from dagster._daemon.monitoring.concurrency import execute_concurrency_slots_iteration
from dagster._seven.compat.pendulum import create_pendulum_time, pendulum_test


@pytest.fixture
def instance():
    with tempfile.TemporaryDirectory() as temp_dir:
        with instance_for_test(
            overrides={
                "event_log_storage": {
                    "module": "dagster.utils.test",
                    "class": "ConcurrencyEnabledSqliteTestEventLogStorage",
                    "config": {"base_dir": temp_dir},
                },
                "run_monitoring": {"enabled": True, "free_slots_after_run_end_seconds": 60},
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


def test_global_concurrency_release(
    instance: DagsterInstance,
    workspace_context: WorkspaceProcessContext,
    logger: Logger,
):
    instance.event_log_storage.set_concurrency_slots("foo", 1)
    freeze_datetime = create_pendulum_time(
        year=2023,
        month=2,
        day=27,
        tz="UTC",
    )

    with pendulum_test(freeze_datetime):
        run = create_run_for_test(instance, job_name="my_job", status=DagsterRunStatus.STARTING)
        instance.event_log_storage.claim_concurrency_slot("foo", run.run_id, "my_step")
        key_info = instance.event_log_storage.get_concurrency_info("foo")
        assert key_info.slot_count == 1
        assert key_info.active_slot_count == 1
        instance.report_run_canceled(run)

        freeze_datetime = freeze_datetime.add(seconds=59)
    with pendulum_test(freeze_datetime):
        list(execute_concurrency_slots_iteration(workspace_context, logger))
        key_info = instance.event_log_storage.get_concurrency_info("foo")
        assert key_info.slot_count == 1
        assert key_info.active_slot_count == 1

        freeze_datetime = freeze_datetime.add(seconds=2)
    with pendulum_test(freeze_datetime):
        list(execute_concurrency_slots_iteration(workspace_context, logger))
        key_info = instance.event_log_storage.get_concurrency_info("foo")
        assert key_info.slot_count == 1
        assert key_info.active_slot_count == 0
