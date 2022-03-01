import multiprocessing

import pendulum
import pytest

from dagster.core.execution.backfill import BulkActionStatus, PartitionBackfill
from dagster.core.instance import DagsterInstance
from dagster.core.test_utils import (
    cleanup_test_instance,
    create_test_daemon_workspace,
    get_crash_signals,
    get_logger_output_from_capfd,
)
from dagster.daemon import get_default_daemon_logger
from dagster.daemon.backfill import execute_backfill_iteration
from dagster.seven import IS_WINDOWS
from dagster.seven.compat.pendulum import create_pendulum_time, to_timezone

from .test_backfill import default_repo, instance_for_context, workspace_load_target

spawn_ctx = multiprocessing.get_context("spawn")


def _test_backfill_in_subprocess(instance_ref, debug_crash_flags):
    execution_datetime = to_timezone(
        create_pendulum_time(
            year=2021,
            month=2,
            day=17,
        ),
        "US/Central",
    )
    with DagsterInstance.from_ref(instance_ref) as instance:
        try:
            with pendulum.test(execution_datetime), create_test_daemon_workspace(
                workspace_load_target=workspace_load_target()
            ) as workspace:
                list(
                    execute_backfill_iteration(
                        instance,
                        workspace,
                        get_default_daemon_logger("BackfillDaemon"),
                        debug_crash_flags=debug_crash_flags,
                    )
                )
        finally:
            cleanup_test_instance(instance)


@pytest.mark.skipif(
    IS_WINDOWS, reason="Windows keeps resources open after termination in a flaky way"
)
def test_simple(capfd):
    with instance_for_context(default_repo) as (
        instance,
        _grpc_server_registry,
        external_repo,
    ):
        external_partition_set = external_repo.get_external_partition_set("simple_partition_set")
        instance.add_backfill(
            PartitionBackfill(
                backfill_id="simple",
                partition_set_origin=external_partition_set.get_external_origin(),
                status=BulkActionStatus.REQUESTED,
                partition_names=["one", "two", "three"],
                from_failure=False,
                reexecution_steps=None,
                tags=None,
                backfill_timestamp=pendulum.now().timestamp(),
            )
        )
        launch_process = spawn_ctx.Process(
            target=_test_backfill_in_subprocess,
            args=[instance.get_ref(), None],
        )
        launch_process.start()
        launch_process.join(timeout=60)
        backfill = instance.get_backfill("simple")
        assert backfill.status == BulkActionStatus.COMPLETED
        assert (
            get_logger_output_from_capfd(capfd, "dagster.daemon.BackfillDaemon")
            == """2021-02-16 18:00:00 -0600 - dagster.daemon.BackfillDaemon - INFO - Starting backfill for simple
2021-02-16 18:00:00 -0600 - dagster.daemon.BackfillDaemon - INFO - Backfill completed for simple for 3 partitions"""
        )


@pytest.mark.skipif(
    IS_WINDOWS, reason="Windows keeps resources open after termination in a flaky way"
)
@pytest.mark.parametrize("crash_signal", get_crash_signals())
def test_before_submit(crash_signal, capfd):
    with instance_for_context(default_repo) as (
        instance,
        _grpc_server_registry,
        external_repo,
    ):
        external_partition_set = external_repo.get_external_partition_set("simple_partition_set")
        instance.add_backfill(
            PartitionBackfill(
                backfill_id="simple",
                partition_set_origin=external_partition_set.get_external_origin(),
                status=BulkActionStatus.REQUESTED,
                partition_names=["one", "two", "three"],
                from_failure=False,
                reexecution_steps=None,
                tags=None,
                backfill_timestamp=pendulum.now().timestamp(),
            )
        )
        launch_process = spawn_ctx.Process(
            target=_test_backfill_in_subprocess,
            args=[instance.get_ref(), {"BEFORE_SUBMIT": crash_signal}],
        )
        launch_process.start()
        launch_process.join(timeout=60)
        assert launch_process.exitcode != 0
        assert (
            get_logger_output_from_capfd(capfd, "dagster.daemon.BackfillDaemon")
            == """2021-02-16 18:00:00 -0600 - dagster.daemon.BackfillDaemon - INFO - Starting backfill for simple"""
        )

        backfill = instance.get_backfill("simple")
        assert backfill.status == BulkActionStatus.REQUESTED
        assert instance.get_runs_count() == 0

        # resume backfill
        launch_process = spawn_ctx.Process(
            target=_test_backfill_in_subprocess,
            args=[instance.get_ref(), None],
        )
        launch_process.start()
        launch_process.join(timeout=60)
        assert (
            get_logger_output_from_capfd(capfd, "dagster.daemon.BackfillDaemon")
            == """2021-02-16 18:00:00 -0600 - dagster.daemon.BackfillDaemon - INFO - Starting backfill for simple
2021-02-16 18:00:00 -0600 - dagster.daemon.BackfillDaemon - INFO - Backfill completed for simple for 3 partitions"""
        )

        backfill = instance.get_backfill("simple")
        assert backfill.status == BulkActionStatus.COMPLETED
        assert instance.get_runs_count() == 3


@pytest.mark.skipif(
    IS_WINDOWS, reason="Windows keeps resources open after termination in a flaky way"
)
@pytest.mark.parametrize("crash_signal", get_crash_signals())
def test_crash_after_submit(crash_signal, capfd):
    with instance_for_context(default_repo) as (
        instance,
        _grpc_server_registry,
        external_repo,
    ):
        external_partition_set = external_repo.get_external_partition_set("simple_partition_set")
        instance.add_backfill(
            PartitionBackfill(
                backfill_id="simple",
                partition_set_origin=external_partition_set.get_external_origin(),
                status=BulkActionStatus.REQUESTED,
                partition_names=["one", "two", "three"],
                from_failure=False,
                reexecution_steps=None,
                tags=None,
                backfill_timestamp=pendulum.now().timestamp(),
            )
        )
        launch_process = spawn_ctx.Process(
            target=_test_backfill_in_subprocess,
            args=[instance.get_ref(), {"AFTER_SUBMIT": crash_signal}],
        )
        launch_process.start()
        launch_process.join(timeout=60)
        assert launch_process.exitcode != 0
        assert (
            get_logger_output_from_capfd(capfd, "dagster.daemon.BackfillDaemon")
            == """2021-02-16 18:00:00 -0600 - dagster.daemon.BackfillDaemon - INFO - Starting backfill for simple"""
        )

        backfill = instance.get_backfill("simple")
        assert backfill.status == BulkActionStatus.REQUESTED
        assert instance.get_runs_count() == 3

        # resume backfill
        launch_process = spawn_ctx.Process(
            target=_test_backfill_in_subprocess,
            args=[instance.get_ref(), None],
        )
        launch_process.start()
        launch_process.join(timeout=60)
        assert (
            get_logger_output_from_capfd(capfd, "dagster.daemon.BackfillDaemon")
            == """2021-02-16 18:00:00 -0600 - dagster.daemon.BackfillDaemon - INFO - Starting backfill for simple
2021-02-16 18:00:00 -0600 - dagster.daemon.BackfillDaemon - INFO - Found 3 existing runs for backfill simple, skipping
2021-02-16 18:00:00 -0600 - dagster.daemon.BackfillDaemon - INFO - Backfill completed for simple for 3 partitions"""
        )

        backfill = instance.get_backfill("simple")
        assert backfill.status == BulkActionStatus.COMPLETED
        assert instance.get_runs_count() == 3
