import weakref
from unittest.mock import MagicMock, patch

import pytest
from dagster import DagsterRunStatus
from dagster._core.launcher import WorkerStatus
from dagster._core.launcher.base import ResumeRunContext
from dagster_celery.launcher import CeleryRunLauncher
from dagster_celery.tags import DAGSTER_CELERY_TASK_ID_TAG


@pytest.fixture
def mock_celery_app():
    app = MagicMock()
    app.AsyncResult.return_value = MagicMock()
    return app


@pytest.fixture
def launcher(mock_celery_app):
    """Create a CeleryRunLauncher with a mocked Celery app."""
    with patch.object(CeleryRunLauncher, "__init__", lambda self: None):
        obj = CeleryRunLauncher.__new__(CeleryRunLauncher)
        obj.celery = mock_celery_app
        # _instance is a read-only property backed by a weakref on MayHaveInstanceWeakref
        mock_instance = MagicMock()
        obj._instance_weakref = weakref.ref(mock_instance)  # noqa: SLF001
        obj._mock_instance_ref = mock_instance  # noqa: SLF001  # keep strong ref alive
        obj.default_queue = "dagster"
        return obj


def _make_run(status=DagsterRunStatus.STARTED, task_id="test-task-123"):
    run = MagicMock()
    run.run_id = "test-run-id"
    run.status = status
    run.tags = {DAGSTER_CELERY_TASK_ID_TAG: task_id}
    run.job_code_origin = MagicMock()
    return run


class TestResumeRun:
    def test_resume_run_calls_create_resume_job_task_with_celery_app(self, launcher):
        """resume_run must pass self.celery (the Celery app), not args, to create_resume_job_task."""
        run = _make_run()
        context = ResumeRunContext(dagster_run=run, workspace=None, resume_attempt_number=1)

        with (
            patch("dagster_celery.launcher.create_resume_job_task") as mock_create,
            # Patch ResumeRunArgs so job_code_origin doesn't need to be a real JobPythonOrigin
            patch("dagster_celery.launcher.ResumeRunArgs"),
            # Patch pack_value and _launch_celery_task_run to isolate the unit under test
            patch("dagster_celery.launcher.pack_value"),
            patch.object(CeleryRunLauncher, "_launch_celery_task_run"),
        ):
            mock_task = MagicMock()
            mock_task.si.return_value = MagicMock()
            mock_task.si.return_value.apply_async.return_value = MagicMock(task_id="new-task-id")
            mock_create.return_value = mock_task

            launcher.resume_run(context)

            # The first positional arg must be the Celery app, not ResumeRunArgs
            mock_create.assert_called_once_with(launcher.celery)

            # The task signature must use resume_job_args_packed (not execute_job_args_packed)
            call_kwargs = mock_task.si.call_args.kwargs
            assert "resume_job_args_packed" in call_kwargs, (
                f"Expected 'resume_job_args_packed' kwarg, got: {list(call_kwargs.keys())}"
            )


class TestCheckRunWorkerHealth:
    def test_task_success_returns_success(self, launcher, mock_celery_app):
        run = _make_run()
        result = mock_celery_app.AsyncResult.return_value
        result.state = "SUCCESS"

        health = launcher.check_run_worker_health(run)
        assert health.status == WorkerStatus.SUCCESS

    def test_task_failure_returns_failed(self, launcher, mock_celery_app):
        run = _make_run()
        result = mock_celery_app.AsyncResult.return_value
        result.state = "FAILURE"

        health = launcher.check_run_worker_health(run)
        assert health.status == WorkerStatus.FAILED

    def test_task_pending_returns_unknown(self, launcher, mock_celery_app):
        run = _make_run()
        result = mock_celery_app.AsyncResult.return_value
        result.state = "PENDING"

        health = launcher.check_run_worker_health(run)
        assert health.status == WorkerStatus.UNKNOWN

    def test_task_started_worker_alive_returns_running(self, launcher, mock_celery_app):
        """When Celery says STARTED and the worker responds to ping, return RUNNING."""
        run = _make_run()
        result = mock_celery_app.AsyncResult.return_value
        result.state = "STARTED"
        result.info = {"hostname": "celery@worker-pod-1"}

        # Worker responds to ping
        inspect_mock = MagicMock()
        inspect_mock.ping.return_value = {"celery@worker-pod-1": {"ok": "pong"}}
        mock_celery_app.control.inspect.return_value = inspect_mock

        health = launcher.check_run_worker_health(run)
        assert health.status == WorkerStatus.RUNNING

    def test_task_started_worker_dead_returns_failed(self, launcher, mock_celery_app):
        """When Celery says STARTED but the worker doesn't respond to ping, return FAILED."""
        run = _make_run()
        result = mock_celery_app.AsyncResult.return_value
        result.state = "STARTED"
        result.info = {"hostname": "celery@worker-pod-1"}

        # Worker does NOT respond to ping
        inspect_mock = MagicMock()
        inspect_mock.ping.return_value = None
        mock_celery_app.control.inspect.return_value = inspect_mock

        health = launcher.check_run_worker_health(run)
        assert health.status == WorkerStatus.FAILED
        assert "not responding" in health.msg.lower()

    def test_task_started_no_worker_info_returns_running(self, launcher, mock_celery_app):
        """When worker hostname is unavailable, fall back to trusting Celery state."""
        run = _make_run()
        result = mock_celery_app.AsyncResult.return_value
        result.state = "STARTED"
        result.info = None

        health = launcher.check_run_worker_health(run)
        assert health.status == WorkerStatus.RUNNING

    def test_task_started_inspect_raises_returns_running(self, launcher, mock_celery_app):
        """When inspect API fails (broker issue), fall back to trusting Celery state."""
        run = _make_run()
        result = mock_celery_app.AsyncResult.return_value
        result.state = "STARTED"
        result.info = {"hostname": "celery@worker-pod-1"}

        # Inspect raises an exception
        mock_celery_app.control.inspect.side_effect = Exception("Broker connection failed")

        health = launcher.check_run_worker_health(run)
        assert health.status == WorkerStatus.RUNNING
