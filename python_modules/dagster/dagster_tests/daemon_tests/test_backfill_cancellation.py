import logging
import sys
import threading
from concurrent.futures import ThreadPoolExecutor, TimeoutError
from unittest import mock

import dagster as dg
import pytest
from dagster._core.events import DagsterEventType
from dagster._core.execution.backfill import cancel_backfill_runs_and_cancellation_complete
from dagster._core.remote_origin import (
    InProcessCodeLocationOrigin,
    RemoteJobOrigin,
    RemoteRepositoryOrigin,
)
from dagster._core.storage.dagster_run import DagsterRunStatus
from dagster._core.storage.tags import BACKFILL_ID_TAG
from dagster._core.test_utils import create_run_for_test
from dagster._core.types.loadable_target_origin import LoadableTargetOrigin

BACKFILL_ID = "backfill"
# Queued runs must have a remote job origin. It is never loaded by these tests.
FAKE_JOB_ORIGIN = RemoteJobOrigin(
    RemoteRepositoryOrigin(
        InProcessCodeLocationOrigin(
            LoadableTargetOrigin(executable_path=sys.executable, module_name="fake")
        ),
        "foo_repo",
    ),
    "foo",
)
logger = logging.getLogger("test_backfill_cancellation")


def _create_backfill_runs(
    instance: dg.DagsterInstance, status: DagsterRunStatus, count: int
) -> list[str]:
    return [
        create_run_for_test(
            instance,
            job_name="foo",
            status=status,
            tags={BACKFILL_ID_TAG: BACKFILL_ID},
            remote_job_origin=FAKE_JOB_ORIGIN,
        ).run_id
        for _ in range(count)
    ]


@pytest.fixture
def instance():
    with dg.instance_for_test() as instance:
        yield instance


@pytest.mark.parametrize("use_threadpool", [False, True])
def test_backfill_runs_are_canceled(instance: dg.DagsterInstance, use_threadpool: bool):
    queued_run_ids = _create_backfill_runs(instance, DagsterRunStatus.QUEUED, 6)
    started_run_ids = _create_backfill_runs(instance, DagsterRunStatus.STARTED, 6)
    thread_ids: set[int] = set()
    lock = threading.Lock()

    def _terminate(run_id: str) -> bool:
        with lock:
            thread_ids.add(threading.get_ident())
        run = instance.get_run_by_id(run_id)
        assert run
        instance.report_run_canceling(run)
        return True

    with (
        ThreadPoolExecutor(max_workers=4) as threadpool_executor,
        mock.patch.object(instance.run_launcher, "terminate", side_effect=_terminate) as terminate,
    ):
        # Queued runs are canceled first, then started runs, in the same call.
        assert not cancel_backfill_runs_and_cancellation_complete(
            instance,
            BACKFILL_ID,
            logger,
            threadpool_executor=threadpool_executor if use_threadpool else None,
        )

    assert sorted(call.args[0] for call in terminate.call_args_list) == sorted(started_run_ids)
    if use_threadpool:
        assert threading.get_ident() not in thread_ids
    else:
        assert thread_ids == {threading.get_ident()}

    for run_id in queued_run_ids:
        run = instance.get_run_by_id(run_id)
        assert run and run.status == DagsterRunStatus.CANCELED
        event_types = [
            record.event_log_entry.get_dagster_event().event_type
            for record in instance.get_records_for_run(run_id).records
            if record.event_log_entry.is_dagster_event
        ]
        assert event_types[-2:] == [
            DagsterEventType.RUN_CANCELING,
            DagsterEventType.RUN_CANCELED,
        ]
    for run_id in started_run_ids:
        run = instance.get_run_by_id(run_id)
        assert run and run.status == DagsterRunStatus.CANCELING


def test_cancel_error_is_raised_with_threadpool(instance: dg.DagsterInstance):
    _create_backfill_runs(instance, DagsterRunStatus.STARTED, 3)

    with (
        ThreadPoolExecutor(max_workers=4) as threadpool_executor,
        mock.patch.object(
            instance.run_launcher, "terminate", side_effect=Exception("terminate failed")
        ),
    ):
        with pytest.raises(Exception, match="terminate failed"):
            cancel_backfill_runs_and_cancellation_complete(
                instance, BACKFILL_ID, logger, threadpool_executor=threadpool_executor
            )


def test_cancellation_waits_for_inflight_work_before_raising(instance: dg.DagsterInstance):
    run_ids = _create_backfill_runs(instance, DagsterRunStatus.STARTED, 2)
    slow_started = threading.Event()
    release_slow = threading.Event()

    def terminate(run_id: str) -> bool:
        if run_id == run_ids[0]:
            assert slow_started.wait(5)
            raise RuntimeError("termination failed")
        slow_started.set()
        assert release_slow.wait(5)
        run = instance.get_run_by_id(run_id)
        assert run
        instance.report_run_canceling(run)
        return True

    with (
        ThreadPoolExecutor(2) as pool,
        ThreadPoolExecutor(1) as callers,
        mock.patch.object(instance.run_launcher, "terminate", side_effect=terminate),
    ):
        future = callers.submit(
            cancel_backfill_runs_and_cancellation_complete,
            instance,
            BACKFILL_ID,
            logger,
            pool,
        )
        try:
            assert slow_started.wait(5)
            with pytest.raises(TimeoutError):
                future.result(timeout=0.1)
        finally:
            release_slow.set()
        with pytest.raises(RuntimeError, match="termination failed"):
            future.result(timeout=5)
        run = instance.get_run_by_id(run_ids[1])
        assert run and run.status == DagsterRunStatus.CANCELING
