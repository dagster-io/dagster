from dagster_examples.toys.pandas_hello_world import (
    pandas_hello_world_pipeline,
    pandas_hello_world_pipeline_no_config,
)

from dagster import execute_pipeline, file_relative_path


def test_execute_pandas_hello_world_pipeline():
    environment = {
        'solids': {
            'sum_solid': {
                'inputs': {'num_df': {'csv': {'path': file_relative_path(__file__, 'num.csv')}}}
            }
        }
    }

    result = execute_pipeline(pandas_hello_world_pipeline, environment_dict=environment)

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
        'sum_sq': [9, 49],
    }


def test_execute_pandas_hello_world_pipeline_no_config():
    environment = {
        'solids': {'read_csv': {'inputs': {'path': file_relative_path(__file__, 'num.csv')}}}
    }

    result = execute_pipeline(pandas_hello_world_pipeline_no_config, environment_dict=environment)

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
        'sum_sq': [9, 49],
    }
