# pylint doesn't know about pytest fixtures
# pylint: disable=unused-argument

import os
import threading
import time
from collections import OrderedDict
from contextlib import contextmanager

import pytest
from click.testing import CliRunner
from dagster_celery import celery_executor
from dagster_celery.cli import main

from dagster import (
    ExecutionTargetHandle,
    ModeDefinition,
    RunConfig,
    default_executors,
    execute_pipeline,
    pipeline,
    seven,
    solid,
)
from dagster.core.definitions.pipeline import PipelineRunsFilter
from dagster.core.instance import DagsterInstance

BUILDKITE = os.getenv('BUILDKITE')
skip_ci = pytest.mark.skipif(
    bool(BUILDKITE),
    reason='Tests hang forever on buildkite for reasons we don\'t currently understand',
)

celery_mode_defs = [ModeDefinition(executor_defs=default_executors + [celery_executor])]


@contextmanager
def start_celery_worker():
    runner = CliRunner()
    runargs = ['worker', 'start', '-d']
    result = runner.invoke(main, runargs)
    assert result.exit_code == 0, str(result.exception)
    try:
        yield
    finally:
        result = runner.invoke(main, ['worker', 'terminate'])
        assert result.exit_code == 0, str(result.exception)


def execute_pipeline_on_celery(tempdir, pipeline_name, tags=None):
    handle = ExecutionTargetHandle.for_pipeline_python_file(__file__, pipeline_name)
    pipeline_def = handle.build_pipeline_definition()
    instance = DagsterInstance.local_temp(tempdir=tempdir)
    return execute_pipeline(
        pipeline_def,
        environment_dict={
            'storage': {'filesystem': {'config': {'base_dir': tempdir}}},
            'execution': {'celery': {}},
        },
        instance=instance,
        run_config=RunConfig(tags=tags),
    )


def execute_eagerly_on_celery(tempdir, pipeline_name, tags=None):
    return execute_pipeline(
        ExecutionTargetHandle.for_pipeline_python_file(
            __file__, pipeline_name
        ).build_pipeline_definition(),
        environment_dict={
            'storage': {'filesystem': {'config': {'base_dir': tempdir}}},
            'execution': {'celery': {'config': {'config_source': {'task_always_eager': True}}}},
        },
        instance=DagsterInstance.local_temp(tempdir=tempdir),
        run_config=RunConfig(tags=tags),
    )


def execute_on_thread(tempdir, pipeline_name, run_priority, done):
    execute_pipeline_on_celery(
        tempdir, pipeline_name, {'dagster-celery/run_priority': run_priority}
    )
    done.set()


@solid(tags={'dagster-celery/priority': 0})
def zero(context):
    assert 'dagster-celery/priority' in context.solid.tags
    assert context.solid.tags['dagster-celery/priority'] == '0'
    context.log.info('Executing with priority 0')
    return True


@solid(tags={'dagster-celery/priority': 1})
def one(context):
    assert 'dagster-celery/priority' in context.solid.tags
    assert context.solid.tags['dagster-celery/priority'] == '1'
    context.log.info('Executing with priority 1')
    return True


@solid(tags={'dagster-celery/priority': 2})
def two(context):
    assert 'dagster-celery/priority' in context.solid.tags
    assert context.solid.tags['dagster-celery/priority'] == '2'
    context.log.info('Executing with priority 2')
    return True


@solid(tags={'dagster-celery/priority': 3})
def three(context):
    assert 'dagster-celery/priority' in context.solid.tags
    assert context.solid.tags['dagster-celery/priority'] == '3'
    context.log.info('Executing with priority 3')
    return True


@solid(tags={'dagster-celery/priority': 4})
def four(context):
    assert 'dagster-celery/priority' in context.solid.tags
    assert context.solid.tags['dagster-celery/priority'] == '4'
    context.log.info('Executing with priority 4')
    return True


@solid(tags={'dagster-celery/priority': 5})
def five(context):
    assert 'dagster-celery/priority' in context.solid.tags
    assert context.solid.tags['dagster-celery/priority'] == '5'
    context.log.info('Executing with priority 5')
    return True


@solid(tags={'dagster-celery/priority': 6})
def six(context):
    assert 'dagster-celery/priority' in context.solid.tags
    assert context.solid.tags['dagster-celery/priority'] == '6'
    context.log.info('Executing with priority 6')
    return True


@solid(tags={'dagster-celery/priority': 7})
def seven_(context):
    assert 'dagster-celery/priority' in context.solid.tags
    assert context.solid.tags['dagster-celery/priority'] == '7'
    context.log.info('Executing with priority 7')
    return True


@solid(tags={'dagster-celery/priority': 8})
def eight(context):
    assert 'dagster-celery/priority' in context.solid.tags
    assert context.solid.tags['dagster-celery/priority'] == '8'
    context.log.info('Executing with priority 8')
    return True


@solid(tags={'dagster-celery/priority': 9})
def nine(context):
    assert 'dagster-celery/priority' in context.solid.tags
    assert context.solid.tags['dagster-celery/priority'] == '9'
    context.log.info('Executing with priority 9')
    return True


@solid(tags={'dagster-celery/priority': 10})
def ten(context):
    assert 'dagster-celery/priority' in context.solid.tags
    assert context.solid.tags['dagster-celery/priority'] == '10'
    context.log.info('Executing with priority 10')
    return True


@pipeline(mode_defs=celery_mode_defs)
def priority_pipeline():
    for i in range(50):
        zero.alias('zero_' + str(i))()
        one.alias('one_' + str(i))()
        two.alias('two_' + str(i))()
        three.alias('three_' + str(i))()
        four.alias('four_' + str(i))()
        five.alias('five_' + str(i))()
        six.alias('six_' + str(i))()
        seven_.alias('seven_' + str(i))()
        eight.alias('eight_' + str(i))()
        nine.alias('nine' + str(i))()
        ten.alias('ten_' + str(i))()


@pytest.mark.skip
@skip_ci
def test_priority_pipeline():
    with seven.TemporaryDirectory() as tempdir:
        result = execute_pipeline_on_celery(tempdir, 'priority_pipeline')
        assert result.success


@pipeline(mode_defs=celery_mode_defs)
def simple_priority_pipeline():
    zero()
    one()
    two()
    three()
    four()
    five()
    six()
    seven_()
    eight()
    nine()
    ten()


@pytest.mark.skip
@skip_ci
def test_eager_priority_pipeline():
    with seven.TemporaryDirectory() as tempdir:
        result = execute_eagerly_on_celery(tempdir, 'simple_priority_pipeline')
        assert result.success
        assert list(OrderedDict.fromkeys([evt.step_key for evt in result.step_event_list])) == [
            'ten.compute',
            'nine.compute',
            'eight.compute',
            'seven_.compute',
            'six.compute',
            'five.compute',
            'four.compute',
            'three.compute',
            'two.compute',
            'one.compute',
            'zero.compute',
        ]


@solid
def sleep_solid(_):
    time.sleep(0.5)
    return True


@pipeline(mode_defs=celery_mode_defs)
def low_pipeline():
    sleep_solid.alias('low_one')()
    sleep_solid.alias('low_two')()
    sleep_solid.alias('low_three')()
    sleep_solid.alias('low_four')()
    sleep_solid.alias('low_five')()


@pipeline(mode_defs=celery_mode_defs)
def hi_pipeline():
    sleep_solid.alias('hi_one')()
    sleep_solid.alias('hi_two')()
    sleep_solid.alias('hi_three')()
    sleep_solid.alias('hi_four')()
    sleep_solid.alias('hi_five')()


@skip_ci
def test_run_priority_pipeline():
    with seven.TemporaryDirectory() as tempdir:
        instance = DagsterInstance.local_temp(tempdir)

        low_done = threading.Event()
        hi_done = threading.Event()

        # enqueue low-priority tasks
        low_thread = threading.Thread(
            target=execute_on_thread, args=(tempdir, 'low_pipeline', -3, low_done)
        )
        low_thread.daemon = True
        low_thread.start()

        time.sleep(1)  # sleep so that we don't hit any sqlite concurrency issues

        # enqueue hi-priority tasks
        hi_thread = threading.Thread(
            target=execute_on_thread, args=(tempdir, 'hi_pipeline', 3, hi_done)
        )
        hi_thread.daemon = True
        hi_thread.start()

        time.sleep(5)  # sleep to give queue time to prioritize tasks

        with start_celery_worker():
            while not low_done.is_set() or not hi_done.is_set():
                time.sleep(1)

            low_runs = instance.get_runs(filters=PipelineRunsFilter(pipeline_name='low_pipeline'))
            assert len(low_runs) == 1
            low_run = low_runs[0]
            lowstats = instance.get_run_stats(low_run.run_id)
            hi_runs = instance.get_runs(filters=PipelineRunsFilter(pipeline_name='hi_pipeline'))
            assert len(hi_runs) == 1
            hi_run = hi_runs[0]
            histats = instance.get_run_stats(hi_run.run_id)

            assert lowstats.start_time < histats.start_time
            assert lowstats.end_time > histats.end_time
