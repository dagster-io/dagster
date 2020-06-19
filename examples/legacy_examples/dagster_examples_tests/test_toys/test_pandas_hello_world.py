import pandas as pd
from dagster_examples.toys.pandas_hello_world import (
    pandas_hello_world_pipeline,
    pandas_hello_world_pipeline_with_read_csv,
    sum_solid,
)

from dagster import execute_pipeline, execute_solid, file_relative_path


def test_execute_pandas_hello_world_solid():
    result = execute_solid(
        sum_solid, input_values={'num_df': pd.DataFrame.from_dict({'num1': [1], 'num2': [2]})}
    )

    assert result.output_value().to_dict('list') == {'num1': [1], 'num2': [2], 'sum': [3]}


def test_execute_pandas_hello_world_pipeline():
    environment = {
        'solids': {
            'sum_solid': {
                'inputs': {'num_df': {'csv': {'path': file_relative_path(__file__, 'num.csv')}}}
            },
            'mult_solid': {
                'inputs': {'num_df': {'csv': {'path': file_relative_path(__file__, 'num.csv')}}}
            },
        }
    }

    result = execute_pipeline(pandas_hello_world_pipeline, run_config=environment)

    assert result.success

    assert result.result_for_solid('sum_solid').output_value().to_dict('list') == {
        'num1': [1, 3],
        'num2': [2, 4],
        'sum': [3, 7],
    }

    assert result.result_for_solid('sum_sq_solid').output_value().to_dict('list') == {
        'num1': [1, 3],
        'num2': [2, 4],
        'sum': [3, 7],
        'sum_mult_sq': [6, 84],
        'sum_sq': [9, 49],
    }


def test_execute_pandas_hello_world_pipeline_with_read_csv():
    environment = {
        'solids': {'read_csv': {'inputs': {'path': file_relative_path(__file__, 'num.csv')}}}
    }

    result = execute_pipeline(pandas_hello_world_pipeline_with_read_csv, run_config=environment)

    assert result.success

    assert result.result_for_solid('sum_solid').output_value().to_dict('list') == {
        'num1': [1, 3],
        'num2': [2, 4],
        'sum': [3, 7],
    }

    assert result.result_for_solid('sum_sq_solid').output_value().to_dict('list') == {
        'num1': [1, 3],
        'num2': [2, 4],
        'sum': [3, 7],
        'sum_mult_sq': [6, 84],
        'sum_sq': [9, 49],
    }


def test_execute_hello_world_with_preset_test():
    assert execute_pipeline(pandas_hello_world_pipeline, preset='test').success


def test_execute_hello_world_with_preset_prod():
    assert execute_pipeline(pandas_hello_world_pipeline, preset='prod').success
