import sys

import pytest

import dagstermill as dm

from dagster import (
    DependencyDefinition,
    Field,
    InputDefinition,
    OutputDefinition,
    PipelineDefinition,
    SolidDefinition,
    SolidInstance,
    check,
    execute_pipeline,
    lambda_solid,
    solid,
    types,
)

from dagster.utils import script_relative_path


def nb_test_path(name):
    return script_relative_path('notebooks/{name}.ipynb'.format(name=name))


def define_hello_world_pipeline():
    return PipelineDefinition(name='hello_world_pipeline', solids=[define_hello_world_solid()])


def define_hello_world_solid():
    return dm.define_dagstermill_solid('hello_world', nb_test_path('hello_world'))


def define_hello_world_with_output():
    return dm.define_dagstermill_solid(
        'hello_world_output', nb_test_path('hello_world_output'), [], [OutputDefinition()]
    )


# Notebooks encode what version of python (e.g. their kernel)
# they run on, so we can't run notebooks in python2 atm
def notebook_test(f):
    return pytest.mark.skipif(
        sys.version_info < (3, 5),
        reason='''Notebooks execute in their own process and hardcode what "kernel" they use.
        All of the development notebooks currently use the python3 "kernel" so they will
        not be executable in a container that only have python2.7 (e.g. in CircleCI)
        ''',
    )(f)


def define_hello_world_with_output_pipeline():
    return PipelineDefinition(
        name='hello_world_with_output_pipeline', solids=[define_hello_world_with_output()]
    )


@notebook_test
def test_hello_world():
    result = execute_pipeline(define_hello_world_pipeline())
    assert result.success


@notebook_test
def test_hello_world_with_output():
    pipeline = define_hello_world_with_output_pipeline()
    result = execute_pipeline(pipeline)
    assert result.success
    assert result.result_for_solid('hello_world_output').transformed_value() == 'hello, world'


# This probably should be moved to a library because it is immensely useful for testing
def solid_definition(fn):
    return check.inst(fn(), SolidDefinition)


@solid_definition
def add_two_numbers_pm_solid():
    return dm.define_dagstermill_solid(
        'add_two_numbers',
        nb_test_path('add_two_numbers'),
        [
            InputDefinition(name='a', dagster_type=types.Int),
            InputDefinition(name='b', dagster_type=types.Int),
        ],
        [OutputDefinition(types.Int)],
    )


@solid_definition
def mult_two_numbers_pm_solid():
    return dm.define_dagstermill_solid(
        'mult_two_numbers',
        nb_test_path('mult_two_numbers'),
        [
            InputDefinition(name='a', dagster_type=types.Int),
            InputDefinition(name='b', dagster_type=types.Int),
        ],
        [OutputDefinition(types.Int)],
    )


@lambda_solid
def return_one():
    return 1


@lambda_solid
def return_two():
    return 2


def define_add_pipeline():
    add_two_numbers = add_two_numbers_pm_solid
    return PipelineDefinition(
        name='test_add_pipeline',
        solids=[return_one, return_two, add_two_numbers],
        dependencies={
            add_two_numbers.name: {
                'a': DependencyDefinition('return_one'),
                'b': DependencyDefinition('return_two'),
            }
        },
    )


@notebook_test
def test_add_pipeline():
    pipeline = define_add_pipeline()
    result = execute_pipeline(
        pipeline, {'context': {'default': {'config': {'log_level': 'ERROR'}}}}
    )
    assert result.success
    assert result.result_for_solid('add_two_numbers').transformed_value() == 3


@solid(inputs=[], config_field=Field(types.Int))
def load_constant(info):
    return info.config


def define_test_notebook_dag_pipeline():
    return PipelineDefinition(
        name='test_notebook_dag',
        solids=[load_constant, add_two_numbers_pm_solid, mult_two_numbers_pm_solid],
        dependencies={
            SolidInstance('load_constant', alias='load_a'): {},
            SolidInstance('load_constant', alias='load_b'): {},
            SolidInstance(name='add_two_numbers', alias='add_two'): {
                'a': DependencyDefinition('load_a'),
                'b': DependencyDefinition('load_b'),
            },
            SolidInstance(name='mult_two_numbers', alias='mult_two'): {
                'a': DependencyDefinition('add_two'),
                'b': DependencyDefinition('load_b'),
            },
        },
    )


@notebook_test
def test_notebook_dag():
    pipeline_result = execute_pipeline(
        define_test_notebook_dag_pipeline(),
        environment={'solids': {'load_a': {'config': 1}, 'load_b': {'config': 2}}},
    )
    assert pipeline_result.success
    assert pipeline_result.result_for_solid('add_two').transformed_value() == 3
    assert pipeline_result.result_for_solid('mult_two').transformed_value() == 6
