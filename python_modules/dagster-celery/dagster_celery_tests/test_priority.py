import os
from collections import OrderedDict
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
def execute_eagerly_on_celery(pipeline_name):
    with seven.TemporaryDirectory() as tempdir:
        result = execute_pipeline(
            ExecutionTargetHandle.for_pipeline_python_file(
                __file__, pipeline_name
            ).build_pipeline_definition(),
            environment_dict={
                'storage': {'filesystem': {'config': {'base_dir': tempdir}}},
                'execution': {'celery': {'config': {'config_source': {'task_always_eager': True}}}},
            },
            instance=DagsterInstance.local_temp(tempdir=tempdir),
        )
        yield result


@contextmanager
def start_celery_worker():
    runner = CliRunner()
    result = runner.invoke(main, ['worker', 'start', '-d'])
    assert result.exit_code == 0, str(result.exception)

    yield

    result = runner.invoke(main, ['worker', 'terminate'])
    assert result.exit_code == 0, str(result.exception)


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
    with execute_pipeline_on_celery('priority_pipeline') as result:
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


def test_eager_priority_pipeline():
    with execute_eagerly_on_celery('simple_priority_pipeline') as result:
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
