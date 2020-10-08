import os
from contextlib import contextmanager

import pytest
from click.testing import CliRunner
from dagster_celery.cli import main

from dagster import execute_pipeline, seven
from dagster.core.definitions.reconstructable import ReconstructablePipeline
from dagster.core.instance import DagsterInstance

BUILDKITE = os.getenv("BUILDKITE")

skip_ci = pytest.mark.skipif(
    bool(BUILDKITE),
    reason="Tests hang forever on buildkite for reasons we don't currently understand",
)

REPO_FILE = os.path.join(os.path.dirname(__file__), "repo.py")


@contextmanager
def tempdir_wrapper(tempdir=None):
    if tempdir:
        yield tempdir
    else:
        with seven.TemporaryDirectory() as t:
            yield t


@contextmanager
def execute_pipeline_on_celery(
    pipeline_name, instance=None, run_config=None, tempdir=None, tags=None, subset=None
):

    with tempdir_wrapper(tempdir) as tempdir:
        pipeline_def = ReconstructablePipeline.for_file(
            REPO_FILE, pipeline_name
        ).subset_for_execution(subset)
        instance = instance or DagsterInstance.local_temp(tempdir=tempdir)
        run_config = run_config or {
            "storage": {"filesystem": {"config": {"base_dir": tempdir}}},
            "execution": {"celery": {}},
        }
        result = execute_pipeline(
            pipeline_def, run_config=run_config, instance=instance, tags=tags,
        )
        yield result


@contextmanager
def execute_eagerly_on_celery(pipeline_name, instance=None, tempdir=None, tags=None, subset=None):
    with seven.TemporaryDirectory() as tempdir:
        run_config = {
            "storage": {"filesystem": {"config": {"base_dir": tempdir}}},
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


def execute_on_thread(pipeline_name, done, tempdir=None, tags=None):
    with execute_pipeline_on_celery(pipeline_name, tempdir=tempdir, tags=tags):
        done.set()


@contextmanager
def start_celery_worker(queue=None):
    runner = CliRunner()
    runargs = ["worker", "start", "-d"]
    if queue:
        runargs += ["-q", queue]
    result = runner.invoke(main, runargs)
    assert result.exit_code == 0, str(result.exception)
    try:
        yield
    finally:
        result = runner.invoke(main, ["worker", "terminate"])
        assert result.exit_code == 0, str(result.exception)


def events_of_type(result, event_type):
    return [event for event in result.event_list if event.event_type_value == event_type]
