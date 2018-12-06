import sys

import pytest

import dagstermill as dm

from dagster import (
    DependencyDefinition,
    Field,
    InputDefinition,
    OutputDefinition,
    PipelineDefinition,
    SolidInstance,
    execute_pipeline,
    lambda_solid,
    solid,
    types,
)

from dagster.utils import script_relative_path


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


def define_add_pipeline():
    add_two_numbers = add_two_numbers_pm_solid('add_two_numbers')
    return PipelineDefinition(
        name='test_add_pipeline',
        solids=[return_one, return_two, add_two_numbers],
        dependencies={
            add_two_numbers.name: {
                'a': DependencyDefinition('return_one'),
                'b': DependencyDefinition('return_two'),
            }
        }
    )


@notebook_test
def test_hello_world_inputs():
    pipeline = define_add_pipeline()
    result = execute_pipeline(pipeline)
    assert result.success
    assert result.result_for_solid('add_two_numbers').transformed_value() == 3


def define_hello_world_config_pipeline():
    with_config_solid = dm.define_dagstermill_solid(
        'with_config',
        nb_test_path('hello_world_with_config'),
        [],
        [OutputDefinition()],
        config_field=Field(types.String),
    )
    return PipelineDefinition(name='test_config_dag', solids=[with_config_solid])


@notebook_test
def test_hello_world_config():
    pipeline = define_hello_world_config_pipeline()
    pipeline_result = execute_pipeline(
        pipeline,
        {
            'solids': {
                'with_config': {
                    'config': script_relative_path('num.csv'),
                },
            },
        },
    )

    assert pipeline_result.success
    assert pipeline_result.result_for_solid('with_config').transformed_value() == 100


@solid(
    inputs=[],
    config_field=Field(types.Int),
)
def load_constant(info):
    return info.config


def define_test_notebook_dag_pipeline():
    return PipelineDefinition(
        name='test_notebook_dag',
        solids=[
            load_constant,
            add_two_numbers_pm_solid('adder'),
            mult_two_numbers_pm_solid('multer'),
        ],
        dependencies={
            SolidInstance('load_constant', alias='load_a'): {},
            SolidInstance('load_constant', alias='load_b'): {},
            SolidInstance(name='adder', alias='add_two'): {
                'a': DependencyDefinition('load_a'),
                'b': DependencyDefinition('load_b'),
            },
            SolidInstance(name='multer', alias='mult_two'): {
                'a': DependencyDefinition('add_two'),
                'b': DependencyDefinition('load_b'),
            },
        },
    )


@notebook_test
def test_notebook_dag():
    pipeline_result = execute_pipeline(
        define_test_notebook_dag_pipeline(),
        environment={
            'solids': {
                'load_a': {
                    'config': 1,
                },
                'load_b': {
                    'config': 2,
                },
            },
        },
    )
    assert pipeline_result.success
    assert pipeline_result.result_for_solid('add_two').transformed_value() == 3
    assert pipeline_result.result_for_solid('mult_two').transformed_value() == 6


@notebook_test
def test_demonstrate_solid_include():
    pipeline_result = execute_pipeline(
        PipelineDefinition(
            solids=[
                dm.define_dagstermill_solid(
                    name='demo_include',
                    notebook_path=nb_test_path('demonstrate_solid_include'),
                    outputs=[OutputDefinition()]
                ),
            ],
            dependencies={
                'demo_include': {},
            }
        )
    )

    assert pipeline_result.success
    assert len(pipeline_result.result_list) == 1
    assert pipeline_result.result_for_solid('demo_include').transformed_value() == 1
