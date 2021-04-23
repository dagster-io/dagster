import os
import signal
import subprocess
import tempfile
from contextlib import contextmanager

from dagster import execute_pipeline
from dagster.core.definitions.reconstructable import ReconstructablePipeline
from dagster.core.instance import DagsterInstance
from dagster.core.test_utils import instance_for_test

BUILDKITE = os.getenv("BUILDKITE")


REPO_FILE = os.path.join(os.path.dirname(__file__), "repo.py")


@contextmanager
def tempdir_wrapper(tempdir=None):
    if tempdir:
        yield tempdir
    else:
        with tempfile.TemporaryDirectory() as t:
            yield t


@contextmanager
def _instance_wrapper(instance):
    if instance:
        yield instance
    else:
        with instance_for_test() as instance:
            yield instance


@contextmanager
def execute_pipeline_on_celery(
    pipeline_name, instance=None, run_config=None, tempdir=None, tags=None, subset=None
):
    with tempdir_wrapper(tempdir) as tempdir:
        pipeline_def = ReconstructablePipeline.for_file(
            REPO_FILE, pipeline_name
        ).subset_for_execution(subset)
        with _instance_wrapper(instance) as wrapped_instance:
            run_config = run_config or {
                "intermediate_storage": {"filesystem": {"config": {"base_dir": tempdir}}},
                "execution": {"celery": {}},
            }
            result = execute_pipeline(
                pipeline_def,
                run_config=run_config,
                instance=wrapped_instance,
                tags=tags,
            )
            yield result


@contextmanager
def execute_eagerly_on_celery(pipeline_name, instance=None, tempdir=None, tags=None, subset=None):
    with tempfile.TemporaryDirectory() as tempdir:
        run_config = {
            "intermediate_storage": {"filesystem": {"config": {"base_dir": tempdir}}},
            "execution": {"celery": {"config": {"config_source": {"task_always_eager": True}}}},
        }

        with execute_pipeline_on_celery(
            pipeline_name,
            instance=instance,
            run_config=run_config,
            tempdir=tempdir,
            tags=tags,
            subset=subset,
        ) as result:
            yield result


def execute_on_thread(pipeline_name, done, instance_ref, tempdir=None, tags=None):
    with DagsterInstance.from_ref(instance_ref) as instance:
        with execute_pipeline_on_celery(
            pipeline_name, tempdir=tempdir, tags=tags, instance=instance
        ):
            done.set()


@contextmanager
def start_celery_worker(queue=None):
    process = subprocess.Popen(
        ["dagster-celery", "worker", "start", "-A", "dagster_celery.app"]
        + (["-q", queue] if queue else [])
        + (["--", "--concurrency", "1"])
    )

    try:
        yield
    finally:
        os.kill(process.pid, signal.SIGINT)
        process.wait()
        subprocess.check_output(["dagster-celery", "worker", "terminate"])


def events_of_type(result, event_type):
    return [event for event in result.event_list if event.event_type_value == event_type]
