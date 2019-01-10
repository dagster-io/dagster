import sys

import pandas as pd
import pytest

import dagstermill as dm

from dagster import execute_pipeline
from dagster.utils import script_relative_path

from dagster_pandas.examples import (
    define_pandas_input_transform_test_pipeline,
    define_pandas_source_test_pipeline,
)


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
