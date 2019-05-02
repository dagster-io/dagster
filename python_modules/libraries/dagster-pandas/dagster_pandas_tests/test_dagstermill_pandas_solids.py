import pandas as pd

from dagster import execute_pipeline
from dagster.utils import script_relative_path

from dagster_pandas.examples import define_papermill_pandas_hello_world_pipeline

from dagstermill.test_utils import notebook_test


@notebook_test
def test_papermill_pandas_hello_world_pipeline():
    pipeline = define_papermill_pandas_hello_world_pipeline()
    pipeline_result = execute_pipeline(
        pipeline,
        {
            'solids': {
                'papermill_pandas_hello_world': {
                    'inputs': {'df': {'csv': {'path': script_relative_path('num_prod.csv')}}}
                }
            }
        },
    )
    assert pipeline_result.success
    solid_result = pipeline_result.result_for_solid('papermill_pandas_hello_world')
    expected = pd.read_csv(script_relative_path('num_prod.csv')) + 1
    assert solid_result.transformed_value().equals(expected)
