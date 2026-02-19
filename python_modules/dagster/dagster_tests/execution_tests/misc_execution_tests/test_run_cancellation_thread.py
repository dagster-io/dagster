import threading
from unittest import mock

import pytest
from dagster._core.execution.run_cancellation_thread import _kill_on_cancel
from dagster._core.instance_for_test import instance_for_test
from dagster._core.storage.dagster_run import DagsterRunStatus
from dagster._core.test_utils import create_run_for_test


@pytest.mark.parametrize(
    "run_status",
    [
        DagsterRunStatus.CANCELING,
        DagsterRunStatus.CANCELED,
        DagsterRunStatus.FAILURE,
    ],
)
def test_kill_on_cancel_sends_interrupt_for_terminal_statuses(run_status: DagsterRunStatus):
    with instance_for_test(
        overrides={"run_monitoring": {"cancellation_thread_poll_interval_seconds": 0}}
    ) as instance:
        # Create a run with the target status
        dagster_run = create_run_for_test(instance, status=run_status)
        run_id = dagster_run.run_id

        shutdown_event = threading.Event()

        with mock.patch(
            "dagster._core.execution.run_cancellation_thread.send_interrupt"
        ) as mock_send_interrupt:
            # Run the cancellation thread function directly
            _kill_on_cancel(instance.get_ref(), run_id, shutdown_event)

            # Verify send_interrupt was called
            mock_send_interrupt.assert_called_once()
