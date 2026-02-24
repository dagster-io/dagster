import weakref
from unittest.mock import MagicMock, patch

import pytest
from dagster import DagsterRunStatus
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
