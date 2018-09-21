import os

import pandas as pd

import dagstermill as dm

from dagster import (
    ConfigDefinition,
    DependencyDefinition,
    InputDefinition,
    OutputDefinition,
    PipelineDefinition,
    config,
    define_stub_solid,
    execute_pipeline,
    types,
)

from dagster.utils import script_relative_path

from dagster.pandas import DataFrame

from .test_basic_dagstermill_solids import (
    nb_test_path,
    notebook_test,
)


def define_pandas_input_transform_test_solid():
    return dm.define_dagstermill_solid(
        name='pandas_input_transform_test',
        notebook_path=nb_test_path('pandas_input_transform_test'),
        inputs=[InputDefinition('df', DataFrame)],
        outputs=[OutputDefinition(types.Int)],
    )


def define_pandas_input_transform_test_pipeline():
    in_df = pd.DataFrame({'num': [3, 5, 7]})
    return PipelineDefinition(
        name='input_transform_test_pipeline',
        solids=[
            define_stub_solid('load_df', in_df),
            define_pandas_input_transform_test_solid(),
        ],
        dependencies={
            'pandas_input_transform_test': {
                'df': DependencyDefinition('load_df'),
            },
        },
    )


def define_pandas_source_test_solid():
    return dm.define_dagstermill_solid(
        name='pandas_source_test',
        notebook_path=nb_test_path('pandas_source_test'),
        inputs=[],
        outputs=[OutputDefinition(DataFrame)],
        config_def=ConfigDefinition(types.String),
    )


def define_pandas_source_test_pipeline():
    return PipelineDefinition(
        name='input_transform_test_pipeline',
        solids=[define_pandas_source_test_solid()],
    )


@notebook_test
def test_pandas_input_transform_test_pipeline():
    pipeline = define_pandas_input_transform_test_pipeline()
    pipeline_result = execute_pipeline(pipeline)
    in_df = pd.DataFrame({'num': [3, 5, 7]})
    solid_result = pipeline_result.result_for_solid('pandas_input_transform_test')
    expected_sum_result = ((in_df + 1)['num']).sum()
    sum_result = solid_result.transformed_value()
    assert sum_result == expected_sum_result


@notebook_test
def test_pandas_source_test_pipeline():
    pipeline = define_pandas_source_test_pipeline()
    pipeline_result = execute_pipeline(
        pipeline,
        config.Environment(
            solids={
                'pandas_source_test': config.Solid(script_relative_path('num.csv')),
            },
        ),
    )
    assert pipeline_result.success
    solid_result = pipeline_result.result_for_solid('pandas_source_test')
    expected = pd.read_csv(script_relative_path('num.csv'))
    assert solid_result.transformed_value().equals(expected)


def test_manager_path():
    rooted_manager = dm.define_manager(define_pandas_input_transform_test_solid())
    dirname = os.path.dirname(os.path.abspath(nb_test_path('pandas_input_transform_test')))
    assert rooted_manager.get_path('foo') == os.path.join(dirname, 'foo')

    unrooted_manager = dm.define_manager()
    assert unrooted_manager.get_path('foo') == 'foo'
