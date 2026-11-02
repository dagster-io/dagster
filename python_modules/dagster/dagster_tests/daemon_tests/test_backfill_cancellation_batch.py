import logging
from unittest.mock import PropertyMock, patch

import pytest
from dagster._core.events import DagsterEvent, DagsterEventType
from dagster._core.execution.backfill import cancel_backfill_runs_and_cancellation_complete
from dagster._core.remote_origin import (
    GrpcServerCodeLocationOrigin,
    RemoteJobOrigin,
    RemoteRepositoryOrigin,
)
from dagster._core.storage.dagster_run import DagsterRunStatus
from dagster._core.storage.tags import BACKFILL_ID_TAG
from dagster._core.test_utils import create_run_for_test, instance_for_test


def _queued_run(instance, status=DagsterRunStatus.QUEUED, tags=None):
    return create_run_for_test(
        instance,
        status=status,
        tags=tags,
        remote_job_origin=RemoteJobOrigin(
            RemoteRepositoryOrigin(GrpcServerCodeLocationOrigin("localhost", port=1234), "repo"),
            "job",
        ),
    )


@pytest.mark.parametrize("batch_supported", [False, True])
@pytest.mark.parametrize("page_size", [1, 2, 500])
def test_queued_cancellation_events_and_listeners(batch_supported, page_size):
    with instance_for_test() as instance:
        runs = [
            _queued_run(
                instance, status=DagsterRunStatus.QUEUED, tags={BACKFILL_ID_TAG: "backfill"}
            )
            for _ in range(3)
        ]
        other = _queued_run(instance, status=DagsterRunStatus.QUEUED)
        notifications = []

        def listener(event):
            notifications.append(
                (
                    event.run_id,
                    event.dagster_event_type,
                    instance.get_run_by_id(event.run_id).status,
                )
            )

        for run in runs:
            instance.add_event_listener(run.run_id, listener)
        storage = instance.event_log_storage
        with (
            patch.object(
                type(storage), "supports_run_event_batch", new_callable=PropertyMock
            ) as supported,
            patch.object(
                storage, "store_run_event_batch", wraps=storage.store_run_event_batch
            ) as batch,
            patch("dagster._core.execution.backfill.CANCELABLE_RUNS_BATCH_SIZE", page_size),
            patch.object(instance.run_launcher, "terminate") as terminate,
        ):
            supported.return_value = batch_supported
            assert not cancel_backfill_runs_and_cancellation_complete(
                instance, "backfill", logging.getLogger(__name__)
            )
            assert cancel_backfill_runs_and_cancellation_complete(
                instance, "backfill", logging.getLogger(__name__)
            )
            assert batch.call_count == ((3 + page_size - 1) // page_size if batch_supported else 0)
            terminate.assert_not_called()
        assert instance.get_run_by_id(other.run_id).status == DagsterRunStatus.QUEUED
        assert notifications == [
            (run.run_id, event_type, status)
            for run in runs
            for event_type, status in (
                (DagsterEventType.RUN_CANCELING, DagsterRunStatus.CANCELING),
                (DagsterEventType.RUN_CANCELED, DagsterRunStatus.CANCELED),
            )
        ]
        for run in runs:
            logs = instance.all_logs(run.run_id)
            assert [event.dagster_event_type for event in logs] == [
                DagsterEventType.RUN_CANCELING,
                DagsterEventType.RUN_CANCELED,
            ]
            assert [event.message for event in logs] == [
                "Canceling run from the queue.",
                "This run has been marked as canceled from outside the execution context.",
            ]
            assert instance.get_run_record_by_id(run.run_id).end_time is not None


def test_batch_write_failure_is_not_replayed_as_single_writes():
    with instance_for_test() as instance:
        run = _queued_run(instance, status=DagsterRunStatus.QUEUED)
        storage = instance.event_log_storage
        with (
            patch.object(
                type(storage), "supports_run_event_batch", new_callable=PropertyMock
            ) as supported,
            patch.object(
                storage, "store_run_event_batch", side_effect=RuntimeError("write failed")
            ) as batch,
            patch.object(storage, "store_event") as single,
        ):
            supported.return_value = True
            with pytest.raises(RuntimeError, match="write failed"):
                instance.report_run_cancellation_batch([run])
            batch.assert_called_once()
            single.assert_not_called()
        assert instance.get_run_by_id(run.run_id).status == DagsterRunStatus.QUEUED


def test_run_that_leaves_queue_uses_launcher():
    with instance_for_test() as instance:
        run = _queued_run(
            instance, status=DagsterRunStatus.QUEUED, tags={BACKFILL_ID_TAG: "backfill"}
        )
        get_runs = instance.get_runs

        def racing_get_runs(filters):
            instance.report_dagster_event(
                DagsterEvent(DagsterEventType.RUN_START.value, job_name=run.job_name), run.run_id
            )
            return get_runs(filters)

        def terminate(run_id):
            assert run_id == run.run_id
            instance.report_run_canceling(instance.get_run_by_id(run_id))
            return True

        with (
            patch.object(instance, "get_runs", side_effect=racing_get_runs),
            patch.object(instance.run_launcher, "terminate", side_effect=terminate) as termination,
            patch.object(instance, "report_run_cancellation_batch") as queued,
        ):
            assert not cancel_backfill_runs_and_cancellation_complete(
                instance, "backfill", logging.getLogger(__name__)
            )
            termination.assert_called_once_with(run.run_id)
            queued.assert_called_once_with([])
        assert instance.get_run_by_id(run.run_id).status == DagsterRunStatus.CANCELING
        assert DagsterEventType.RUN_CANCELED not in [
            event.dagster_event_type for event in instance.all_logs(run.run_id)
        ]


def test_empty_cancellation_batch_does_not_write():
    with instance_for_test() as instance:
        storage = instance.event_log_storage
        with (
            patch.object(
                type(storage), "supports_run_event_batch", new_callable=PropertyMock
            ) as supported,
            patch.object(storage, "store_run_event_batch") as batch,
        ):
            supported.return_value = True
            instance.report_run_cancellation_batch([])
            batch.assert_not_called()
