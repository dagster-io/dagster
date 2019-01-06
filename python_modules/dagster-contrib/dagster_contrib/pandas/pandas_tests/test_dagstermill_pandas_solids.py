import sys

import pandas as pd
import pytest

import dagstermill as dm

from dagster import (
    DependencyDefinition,
    InputDefinition,
    OutputDefinition,
    PipelineDefinition,
    RepositoryDefinition,
    define_stub_solid,
    execute_pipeline,
    types,
)

from dagster.utils import script_relative_path

from dagster_contrib.pandas import DataFrame


# dummy commnet


def nb_test_path(name):
    return script_relative_path('notebooks/{name}.ipynb'.format(name=name))


def notebook_test(f):
    # mark this with the "notebook_test" tag so that they can be all be skipped
    # (for performance reasons) and mark them as python3 only
    return pytest.mark.notebook_test(
        pytest.mark.skipif(
            sys.version_info < (3, 5),
            reason='''Notebooks execute in their own process and hardcode what "kernel" they use.
        All of the development notebooks currently use the python3 "kernel" so they will
        not be executable in a container that only have python2.7 (e.g. in CircleCI)
        ''',
        )(f)
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
        solids=[define_stub_solid('load_df', in_df), define_pandas_input_transform_test_solid()],
        dependencies={'pandas_input_transform_test': {'df': DependencyDefinition('load_df')}},
    )


def define_pandas_source_test_solid():
    return dm.define_dagstermill_solid(
        name='pandas_source_test',
        notebook_path=nb_test_path('pandas_source_test'),
        inputs=[InputDefinition(name='df', dagster_type=DataFrame)],
        outputs=[OutputDefinition(DataFrame)],
    )


def define_pandas_repository():
    return RepositoryDefinition(
        name='test_dagstermill_pandas_solids',
        pipeline_dict={'input_transform_test_pipeline': define_pandas_source_test_pipeline},
    )


def define_pandas_source_test_pipeline():
    return PipelineDefinition(
        name='input_transform_test_pipeline',
        solids=[
            define_stub_solid('load_num_csv', pd.read_csv(script_relative_path('num_prod.csv'))),
            define_pandas_source_test_solid(),
        ],
        dependencies={'pandas_source_test': {'df': DependencyDefinition('load_num_csv')}},
    )


@pytest.mark.skip('Must ship over run id to notebook process')
@notebook_test
def test_pandas_input_transform_test_pipeline():
    pipeline = define_pandas_input_transform_test_pipeline()
    pipeline_result = execute_pipeline(
        pipeline,
        {
            'solids': {
                'pandas_source_test': {
                    'inputs': {'df': {'csv': {'path': script_relative_path('num.csv')}}}
                }
            }
        },
    )
    in_df = pd.DataFrame({'num': [3, 5, 7]})
    solid_result = pipeline_result.result_for_solid('pandas_input_transform_test')
    expected_sum_result = ((in_df + 1)['num']).sum()
    sum_result = solid_result.transformed_value()
    assert sum_result == expected_sum_result


@notebook_test
def test_pandas_source_test_pipeline():
    pipeline = define_pandas_source_test_pipeline()
    pipeline_result = execute_pipeline(pipeline)
    assert pipeline_result.success
    solid_result = pipeline_result.result_for_solid('pandas_source_test')
    expected = pd.read_csv(script_relative_path('num_prod.csv')) + 1
    assert solid_result.transformed_value().equals(expected)
