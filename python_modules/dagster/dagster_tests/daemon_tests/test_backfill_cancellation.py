import logging
import sys
import threading
from unittest import mock

import dagster as dg
import pytest
from dagster._core.events import DagsterEventType
from dagster._core.execution import backfill as backfill_module
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


def test_queued_runs_are_canceled_with_batched_event_writes(
    instance: dg.DagsterInstance, monkeypatch: pytest.MonkeyPatch
):
    monkeypatch.setattr(backfill_module, "QUEUED_RUNS_CANCEL_WRITE_BATCH_SIZE", 4)
    run_ids = _create_backfill_runs(instance, DagsterRunStatus.QUEUED, 10)

    with (
        mock.patch.object(
            instance.event_log_storage,
            "store_event_batch",
            wraps=instance.event_log_storage.store_event_batch,
        ) as store_event_batch,
        mock.patch.object(instance.run_launcher, "terminate") as terminate,
    ):
        assert not cancel_backfill_runs_and_cancellation_complete(instance, BACKFILL_ID, logger)

    # 10 runs in batches of 4 runs, with 2 events per run.
    assert [len(call.args[0]) for call in store_event_batch.call_args_list] == [8, 8, 4]
    terminate.assert_not_called()
    for run_id in run_ids:
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

    # All runs are canceled, so the next call reports that cancellation is complete.
    assert cancel_backfill_runs_and_cancellation_complete(instance, BACKFILL_ID, logger)


@pytest.mark.parametrize("max_workers", [1, 4])
def test_started_runs_are_terminated(
    instance: dg.DagsterInstance, monkeypatch: pytest.MonkeyPatch, max_workers: int
):
    monkeypatch.setattr(backfill_module, "TERMINATE_RUNS_MAX_WORKERS", max_workers)
    run_ids = _create_backfill_runs(instance, DagsterRunStatus.STARTED, 6)
    thread_ids: set[int] = set()
    lock = threading.Lock()

    def _terminate(run_id: str) -> bool:
        with lock:
            thread_ids.add(threading.get_ident())
        run = instance.get_run_by_id(run_id)
        assert run
        instance.report_run_canceling(run)
        return True

    with mock.patch.object(instance.run_launcher, "terminate", side_effect=_terminate) as terminate:
        assert not cancel_backfill_runs_and_cancellation_complete(instance, BACKFILL_ID, logger)

    assert sorted(call.args[0] for call in terminate.call_args_list) == sorted(run_ids)
    if max_workers == 1:
        assert thread_ids == {threading.get_ident()}
    for run_id in run_ids:
        run = instance.get_run_by_id(run_id)
        assert run and run.status == DagsterRunStatus.CANCELING


def test_handle_new_event_batch_falls_back_to_single_writes(instance: dg.DagsterInstance):
    run_ids = _create_backfill_runs(instance, DagsterRunStatus.QUEUED, 2)
    runs = [instance.get_run_by_id(run_id) for run_id in run_ids]

    with mock.patch.object(
        instance.event_log_storage, "store_event_batch", side_effect=Exception("batch failed")
    ):
        backfill_module._cancel_queued_runs(instance, runs)  # noqa: SLF001  # ty: ignore[invalid-argument-type]

    for run_id in run_ids:
        run = instance.get_run_by_id(run_id)
        assert run and run.status == DagsterRunStatus.CANCELED
