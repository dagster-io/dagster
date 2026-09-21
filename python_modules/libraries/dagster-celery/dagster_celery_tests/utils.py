import os
import signal
import subprocess
import tempfile
import threading
import time
from collections.abc import Iterator, Mapping, Sequence
from contextlib import contextmanager
from typing import Any

from dagster._core.definitions.reconstruct import ReconstructableJob
from dagster._core.events import DagsterEvent
from dagster._core.execution.api import execute_job
from dagster._core.execution.execution_result import ExecutionResult
from dagster._core.instance import DagsterInstance
from dagster._core.instance.ref import InstanceRef
from dagster._core.test_utils import instance_for_test
from dagster_celery.app import app as celery_app

BUILDKITE = os.getenv("BUILDKITE")


REPO_FILE = os.path.join(os.path.dirname(__file__), "repo.py")


@contextmanager
def tempdir_wrapper(tempdir: str | None = None) -> Iterator[str]:
    if tempdir:
        yield tempdir
    else:
        with tempfile.TemporaryDirectory() as t:
            yield t


@contextmanager
def _instance_wrapper(instance: DagsterInstance | None) -> Iterator[DagsterInstance]:
    if instance:
        yield instance
    else:
        with instance_for_test() as instance:
            yield instance


@contextmanager
def execute_job_on_celery(
    job_name: str,
    instance: DagsterInstance | None = None,
    run_config: Mapping[str, Any] | None = None,
    tempdir: str | None = None,
    tags: Mapping[str, str] | None = None,
    subset: Sequence[str] | None = None,
) -> Iterator[ExecutionResult]:
    with tempdir_wrapper(tempdir) as tempdir:
        job_def = ReconstructableJob.for_file(REPO_FILE, job_name).get_subset(op_selection=subset)
        with _instance_wrapper(instance) as wrapped_instance:
            run_config = run_config or {
                "resources": {"io_manager": {"config": {"base_dir": tempdir}}},
                # "execution": {"celery": {}},
            }
            with execute_job(
                job_def,
                run_config=run_config,
                instance=wrapped_instance,
                tags=tags,
            ) as result:
                yield result


@contextmanager
def execute_eagerly_on_celery(
    job_name: str,
    instance: DagsterInstance | None = None,
    tempdir: str | None = None,
    tags: Mapping[str, str] | None = None,
    subset: Sequence[str] | None = None,
) -> Iterator[ExecutionResult]:
    with tempfile.TemporaryDirectory() as tempdir:
        run_config = {
            "resources": {"io_manager": {"config": {"base_dir": tempdir}}},
            "execution": {"config": {"config_source": {"task_always_eager": True}}},
        }

        with execute_job_on_celery(
            job_name,
            instance=instance,
            run_config=run_config,
            tempdir=tempdir,
            tags=tags,
            subset=subset,
        ) as result:
            yield result


def execute_on_thread(
    job_name: str,
    done: threading.Event,
    instance_ref: InstanceRef,
    tempdir: str | None = None,
    tags: Mapping[str, str] | None = None,
) -> None:
    with DagsterInstance.from_ref(instance_ref) as instance:
        with execute_job_on_celery(job_name, tempdir=tempdir, tags=tags, instance=instance):
            done.set()


@contextmanager
def start_celery_worker(queue: str | None = None) -> Iterator[None]:
    process = subprocess.Popen(
        ["dagster-celery", "worker", "start", "-A", "dagster_celery.app"]
        + (["-q", queue] if queue else [])
        + (["--", "--concurrency", "1"])
    )

    try:
        _wait_for_worker_ready(queue)
        yield
    finally:
        os.kill(process.pid, signal.SIGINT)
        process.wait()
        subprocess.check_output(["dagster-celery", "worker", "terminate"])


def _wait_for_worker_ready(queue: str | None, timeout: float = 60.0) -> None:
    # `subprocess.Popen` returns as soon as the worker process is spawned, but
    # the worker needs to connect to the broker and register before it will
    # dequeue any tasks. Tests that `launch_run` before the worker is ready
    # then race a short event-polling deadline against ~10s of worker startup.
    expected_queue = queue if queue is not None else "dagster"
    deadline = time.monotonic() + timeout
    while time.monotonic() < deadline:
        try:
            active_queues = celery_app.control.inspect(timeout=1.0).active_queues() or {}
        except Exception:
            active_queues = {}
        for queues in active_queues.values():
            if any(q.get("name") == expected_queue for q in queues):
                return
        time.sleep(0.25)
    raise TimeoutError(
        f"Celery worker for queue {expected_queue!r} did not become ready within {timeout:.0f}s"
    )


def events_of_type(result: ExecutionResult, event_type: str) -> Sequence[DagsterEvent]:
    return [event for event in result.all_events if event.event_type_value == event_type]
