import os
import threading
import time
from contextlib import contextmanager

import pytest
from click.testing import CliRunner
from dagster_celery import celery_executor
from dagster_celery.cli import main

from dagster import (
    ExecutionTargetHandle,
    ModeDefinition,
    default_executors,
    execute_pipeline,
    pipeline,
    seven,
    solid,
)
from dagster.core.instance import DagsterInstance

BUILDKITE = os.getenv('BUILDKITE')
skip_ci = pytest.mark.skipif(
    bool(BUILDKITE),
    reason='Tests hang forever on buildkite for reasons we don\'t currently understand',
)

celery_mode_defs = [ModeDefinition(executor_defs=default_executors + [celery_executor])]


@contextmanager
def execute_pipeline_on_celery(pipeline_name):
    with seven.TemporaryDirectory() as tempdir:
        handle = ExecutionTargetHandle.for_pipeline_python_file(__file__, pipeline_name)
        pipeline_def = handle.build_pipeline_definition()
        instance = DagsterInstance.local_temp(tempdir=tempdir)
        result = execute_pipeline(
            pipeline_def,
            environment_dict={
                'storage': {'filesystem': {'config': {'base_dir': tempdir}}},
                'execution': {'celery': {}},
            },
            instance=instance,
        )
        yield result


@contextmanager
def start_celery_worker(queue=None):
    runner = CliRunner()
    runargs = ['worker', 'start', '-d']
    if queue:
        runargs += ['-q', queue]
    result = runner.invoke(main, runargs)
    assert result.exit_code == 0, str(result.exception)
    try:
        yield
    finally:
        result = runner.invoke(main, ['worker', 'terminate'])
        assert result.exit_code == 0, str(result.exception)


@solid(tags={'dagster-celery/queue': 'fooqueue'})
def fooqueue(context):
    assert context.solid.tags['dagster-celery/queue'] == 'fooqueue'
    context.log.info('Executing on queue fooqueue')
    return True


@pipeline(mode_defs=celery_mode_defs)
def multiqueue_pipeline():
    fooqueue()


# @pytest.mark.skip
@skip_ci
def test_multiqueue():
    def execute_on_thread(done):
        with execute_pipeline_on_celery('multiqueue_pipeline') as result:
            assert result.success
            done.set()

    done = threading.Event()
    with start_celery_worker():
        execute_thread = threading.Thread(target=execute_on_thread, args=(done,))
        execute_thread.daemon = True
        execute_thread.start()
        time.sleep(1)
        assert not done.is_set()
        with start_celery_worker(queue='fooqueue'):
            execute_thread.join()
            assert done.is_set()
