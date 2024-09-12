import multiprocessing
import time
from signal import Signals

import pytest
from dagster import DagsterInstance
from dagster._core.execution.backfill import BulkActionStatus, PartitionBackfill
from dagster._core.remote_representation import ExternalRepository
from dagster._core.test_utils import (
    cleanup_test_instance,
    create_test_daemon_workspace_context,
    freeze_time,
    get_crash_signals,
)
from dagster._daemon import get_default_daemon_logger
from dagster._daemon.backfill import execute_backfill_iteration
from dagster._seven import IS_WINDOWS
from dagster._time import create_datetime

from dagster_tests.daemon_tests.conftest import workspace_load_target

spawn_ctx = multiprocessing.get_context("spawn")


def _test_backfill_in_subprocess(instance_ref, debug_crash_flags):
    execution_datetime = create_datetime(
        year=2021,
        month=2,
        day=17,
    )
    with DagsterInstance.from_ref(instance_ref) as instance:
        try:
            with freeze_time(execution_datetime), create_test_daemon_workspace_context(
                workspace_load_target=workspace_load_target(), instance=instance
            ) as workspace_context:
                list(
                    execute_backfill_iteration(
                        workspace_context,
                        get_default_daemon_logger("BackfillDaemon"),
                        debug_crash_flags=debug_crash_flags,
                    )
                )
        finally:
            cleanup_test_instance(instance)


@pytest.mark.skipif(
    IS_WINDOWS, reason="Windows keeps resources open after termination in a flaky way"
)
def test_simple(instance: DagsterInstance, external_repo: ExternalRepository):
    external_partition_set = external_repo.get_external_partition_set("the_job_partition_set")
    instance.add_backfill(
        PartitionBackfill(
            backfill_id="simple",
            partition_set_origin=external_partition_set.get_external_origin(),
            status=BulkActionStatus.REQUESTED,
            partition_names=["one", "two", "three"],
            from_failure=False,
            reexecution_steps=None,
            tags=None,
            backfill_timestamp=time.time(),
        )
    )
    launch_process = spawn_ctx.Process(
        target=_test_backfill_in_subprocess,
        args=[instance.get_ref(), None],
    )
    launch_process.start()
    launch_process.join(timeout=60)
    backfill = instance.get_backfill("simple")
    assert backfill
    assert backfill.status == BulkActionStatus.COMPLETED


@pytest.mark.skipif(
    IS_WINDOWS, reason="Windows keeps resources open after termination in a flaky way"
)
@pytest.mark.parametrize("crash_signal", get_crash_signals())
def test_before_submit(
    crash_signal: Signals, instance: DagsterInstance, external_repo: ExternalRepository
):
    external_partition_set = external_repo.get_external_partition_set("the_job_partition_set")
    instance.add_backfill(
        PartitionBackfill(
            backfill_id="simple",
            partition_set_origin=external_partition_set.get_external_origin(),
            status=BulkActionStatus.REQUESTED,
            partition_names=["one", "two", "three"],
            from_failure=False,
            reexecution_steps=None,
            tags=None,
            backfill_timestamp=time.time(),
        )
    )
    launch_process = spawn_ctx.Process(
        target=_test_backfill_in_subprocess,
        args=[instance.get_ref(), {"BEFORE_SUBMIT": crash_signal}],
    )
    launch_process.start()
    launch_process.join(timeout=60)
    assert launch_process.exitcode != 0

    backfill = instance.get_backfill("simple")
    assert backfill
    assert backfill.status == BulkActionStatus.REQUESTED
    assert instance.get_runs_count() == 0

    # resume backfill
    launch_process = spawn_ctx.Process(
        target=_test_backfill_in_subprocess,
        args=[instance.get_ref(), None],
    )
    launch_process.start()
    launch_process.join(timeout=60)

    backfill = instance.get_backfill("simple")
    assert backfill
    assert backfill.status == BulkActionStatus.COMPLETED
    assert instance.get_runs_count() == 3


@pytest.mark.skipif(
    IS_WINDOWS, reason="Windows keeps resources open after termination in a flaky way"
)
@pytest.mark.parametrize("crash_signal", get_crash_signals())
def test_crash_after_submit(
    crash_signal: Signals, instance: DagsterInstance, external_repo: ExternalRepository
):
    external_partition_set = external_repo.get_external_partition_set("the_job_partition_set")
    instance.add_backfill(
        PartitionBackfill(
            backfill_id="simple",
            partition_set_origin=external_partition_set.get_external_origin(),
            status=BulkActionStatus.REQUESTED,
            partition_names=["one", "two", "three"],
            from_failure=False,
            reexecution_steps=None,
            tags=None,
            backfill_timestamp=time.time(),
        )
    )
    launch_process = spawn_ctx.Process(
        target=_test_backfill_in_subprocess,
        args=[instance.get_ref(), {"AFTER_SUBMIT": crash_signal}],
    )
    launch_process.start()
    launch_process.join(timeout=60)
    assert launch_process.exitcode != 0

    backfill = instance.get_backfill("simple")
    assert backfill
    assert backfill.status == BulkActionStatus.REQUESTED
    assert instance.get_runs_count() == 3

    # resume backfill
    launch_process = spawn_ctx.Process(
        target=_test_backfill_in_subprocess,
        args=[instance.get_ref(), None],
    )
    launch_process.start()
    launch_process.join(timeout=60)

    backfill = instance.get_backfill("simple")
    assert backfill
    assert backfill.status == BulkActionStatus.COMPLETED
    assert instance.get_runs_count() == 3
