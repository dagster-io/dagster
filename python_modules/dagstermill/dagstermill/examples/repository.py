import os
import pandas as pd

import dagstermill as dm

from dagster import (
    DependencyDefinition,
    Field,
    InputDefinition,
    Int,
    OutputDefinition,
    PipelineDefinition,
    RepositoryDefinition,
    SolidDefinition,
    SolidInstance,
    check,
    lambda_solid,
    solid,
    as_dagster_type,
    SerializationStrategy,
)
from dagster_pandas import DataFrame


def nb_test_path(name):
    return os.path.join(
        os.path.dirname(os.path.realpath(__file__)), 'notebooks/{name}.ipynb'.format(name=name)
    )


def define_hello_world_pipeline():
    return PipelineDefinition(name='hello_world_pipeline', solids=[define_hello_world_solid()])


def define_hello_world_solid():
    return dm.define_dagstermill_solid('hello_world', nb_test_path('hello_world'))


def define_hello_world_with_output():
    return dm.define_dagstermill_solid(
        'hello_world_output', nb_test_path('hello_world_output'), [], [OutputDefinition()]
    )


def define_hello_world_with_output_pipeline():
    return PipelineDefinition(
        name='hello_world_with_output_pipeline', solids=[define_hello_world_with_output()]
    )


# This probably should be moved to a library because it is immensely useful for testing
def solid_definition(fn):
    return check.inst(fn(), SolidDefinition)


@solid_definition
def add_two_numbers_pm_solid():
    return dm.define_dagstermill_solid(
        'add_two_numbers',
        nb_test_path('add_two_numbers'),
        [InputDefinition(name='a', dagster_type=Int), InputDefinition(name='b', dagster_type=Int)],
        [OutputDefinition(Int)],
    )


@solid_definition
def mult_two_numbers_pm_solid():
    return dm.define_dagstermill_solid(
        'mult_two_numbers',
        nb_test_path('mult_two_numbers'),
        [InputDefinition(name='a', dagster_type=Int), InputDefinition(name='b', dagster_type=Int)],
        [OutputDefinition(Int)],
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


@solid(inputs=[], config_field=Field(Int))
def load_constant(context):
    return context.solid_config


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


def define_error_pipeline():
    return PipelineDefinition(
        name='error_pipeline',
        solids=[dm.define_dagstermill_solid('error_solid', nb_test_path('error_notebook'))],
    )


@solid_definition
def clean_data_solid():
    return dm.define_dagstermill_solid(
        'clean_data', nb_test_path('clean_data'), outputs=[OutputDefinition(DataFrame)]
    )


@solid_definition
def LR_solid():
    return dm.define_dagstermill_solid(
        'linear_regression',
        nb_test_path('tutorial_LR'),
        inputs=[InputDefinition(name='df', dagster_type=DataFrame)],
    )


@solid_definition
def RF_solid():
    return dm.define_dagstermill_solid(
        'random_forest_regression',
        nb_test_path('tutorial_RF'),
        inputs=[InputDefinition(name='df', dagster_type=DataFrame)],
    )


def define_tutorial_pipeline():
    return PipelineDefinition(
        name='tutorial_pipeline',
        solids=[clean_data_solid, LR_solid, RF_solid],
        dependencies={
            SolidInstance('clean_data'): {},
            SolidInstance('linear_regression'): {'df': DependencyDefinition('clean_data')},
            SolidInstance('random_forest_regression'): {'df': DependencyDefinition('clean_data')},
        },
    )


class ComplexSerializationStrategy(SerializationStrategy):  # pylint: disable=no-init
    def serialize_value(self, context, value, write_file_obj):
        pass

    def deserialize_value(self, context, read_file_obj):
        pass


complex_serialization_strategy = ComplexSerializationStrategy()

ComplexDagsterType = as_dagster_type(
    pd.DataFrame, serialization_strategy=complex_serialization_strategy
)


def no_repo_reg_solid():
    return dm.define_dagstermill_solid(
        'no_repo_reg',
        nb_test_path('no_repo_reg_error'),
        outputs=[OutputDefinition(name='df', dagster_type=ComplexDagsterType)],
    )


def define_no_repo_registration_error_pipeline():
    return PipelineDefinition(name='repo_registration_error', solids=[no_repo_reg_solid()])


def define_example_repository():
    return RepositoryDefinition(
        name='notebook_repo',
        pipeline_dict={
            'error_pipeline': define_error_pipeline,
            'hello_world_pipeline': define_hello_world_pipeline,
            'hello_world_with_output_pipeline': define_hello_world_with_output_pipeline,
            'test_add_pipeline': define_add_pipeline,
            'test_notebook_dag': define_test_notebook_dag_pipeline,
            'tutorial_pipeline': define_tutorial_pipeline,
            'repo_registration_error': define_no_repo_registration_error_pipeline,
        },
    )
