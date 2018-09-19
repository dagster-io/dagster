import sys
import pytest

from dagster import (
    DependencyDefinition,
    InputDefinition,
    OutputDefinition,
    PipelineDefinition,
    config,
    execute_pipeline,
    lambda_solid,
    types,
)

from dagster.utils import script_relative_path

import dagstermill as dm


def test_basic_get_in_memory_input():
    inputs = dm.define_inputs(a=1)
    assert dm.get_input(inputs, 'a') == 1


def test_basic_get_in_memory_inputs():
    inputs = dm.define_inputs(a=1, b=2)
    assert dm.get_input(inputs, 'a') == 1
    assert dm.get_input(inputs, 'b') == 2

    a, b = dm.get_inputs(inputs, 'a', 'b')

    assert a == 1
    assert b == 2


def test_basic_get_serialized_inputs():
    inputs = dm.serialize_dm_object(dict(a=1, b=2))
    assert dm.get_input(inputs, 'a') == 1
    assert dm.get_input(inputs, 'b') == 2

    a, b = dm.get_inputs(inputs, 'a', 'b')

    assert a == 1
    assert b == 2


def test_basic_in_memory_config():
    value = {'path': 'some_path.csv'}
    config_ = dm.define_config(value)
    assert dm.get_config(config_) == value


def test_basic_serialized_config():
    value = {'path': 'some_path.csv'}
    config_ = dm.serialize_dm_object(value)
    assert dm.get_config(config_) == value


def test_serialize_unserialize():
    value = {'a': 1, 'b': 2}
    assert dm.deserialize_dm_object(dm.serialize_dm_object(value)) == value


def nb_test_path(name):
    return script_relative_path('notebooks/{name}.ipynb'.format(name=name))


def define_hello_world_solid():
    return dm.define_dagstermill_solid('test', nb_test_path('hello_world'))


def define_hello_world_with_output():
    return dm.define_dagstermill_solid(
        'test',
        nb_test_path('hello_world_output'),
        [],
        [OutputDefinition()],
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


@notebook_test
def test_hello_world():
    pipeline = PipelineDefinition(solids=[define_hello_world_solid()])
    result = execute_pipeline(pipeline)
    assert result.success


@notebook_test
def test_hello_world_with_output():
    pipeline = PipelineDefinition(solids=[define_hello_world_with_output()])
    result = execute_pipeline(pipeline)
    assert result.success
    assert result.result_for_solid('test').transformed_value() == 'hello, world'


def add_two_numbers_pm_solid(name):
    return dm.define_dagstermill_solid(
        name,
        nb_test_path('add_two_numbers'),
        [
            InputDefinition(name='a', dagster_type=types.Int),
            InputDefinition(name='b', dagster_type=types.Int),
        ],
        [OutputDefinition(types.Int)],
    )


def mult_two_numbers_pm_solid(name):
    return dm.define_dagstermill_solid(
        name,
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


def define_hello_world_inputs_pipeline():
    with_inputs_solid = add_two_numbers_pm_solid('with_inputs')
    return PipelineDefinition(
        solids=[return_one, return_two, with_inputs_solid],
        dependencies={
            with_inputs_solid.name: {
                'a': DependencyDefinition('return_one'),
                'b': DependencyDefinition('return_two'),
            }
        }
    )


@notebook_test
def test_hello_world_inputs():
    pipeline = define_hello_world_inputs_pipeline()
    result = execute_pipeline(pipeline)
    assert result.success
    assert result.result_for_solid('with_inputs').transformed_value() == 3


@notebook_test
def test_hello_world_config():
    with_config_solid = dm.define_dagstermill_solid(
        'with_config',
        nb_test_path('hello_world_with_config'),
        [],
        [OutputDefinition()],
    )

    pipeline = PipelineDefinition(solids=[with_config_solid])
    pipeline_result = execute_pipeline(
        pipeline,
        config.Environment(solids={'with_config': config.Solid(script_relative_path('num.csv'))}),
    )

    assert pipeline_result.success
    assert pipeline_result.result_for_solid('with_config').transformed_value() == 100


def define_test_notebook_dag_pipeline():
    return PipelineDefinition(
        solids=[
            return_one,
            return_two,
            add_two_numbers_pm_solid('add_two'),
            mult_two_numbers_pm_solid('mult_two'),
        ],
        dependencies={
            'add_two': {
                'a': DependencyDefinition('return_one'),
                'b': DependencyDefinition('return_two'),
            },
            'mult_two': {
                'a': DependencyDefinition('add_two'),
                'b': DependencyDefinition('return_two'),
            },
        },
    )


@notebook_test
def test_notebook_dag():
    pipeline_result = execute_pipeline(define_test_notebook_dag_pipeline())
    assert pipeline_result.success
    assert pipeline_result.result_for_solid('add_two').transformed_value() == 3
    assert pipeline_result.result_for_solid('mult_two').transformed_value() == 6
