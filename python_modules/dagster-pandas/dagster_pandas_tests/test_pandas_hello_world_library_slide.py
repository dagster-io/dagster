from dagster import (
    InputDefinition,
    OutputDefinition,
    execute_pipeline,
    lambda_solid,
    PipelineDefinition,
)

from dagster.core.test_utils import single_output_transform

from dagster.utils import script_relative_path

from dagster_pandas import DataFrame


def create_num_csv_environment():
    return {
        'solids': {
            'hello_world': {
                'inputs': {'num_csv': {'csv': {'path': script_relative_path('num.csv')}}}
            }
        }
    }


def test_hello_world_with_dataframe_fns():
    hello_world = create_definition_based_solid()
    run_hello_world(hello_world)


def run_hello_world(hello_world):
    assert len(hello_world.input_defs) == 1

    pipeline = PipelineDefinition(solids=[hello_world], dependencies={'hello_world': {}})

    pipeline_result = execute_pipeline(pipeline, environment_dict=create_num_csv_environment())

    result = pipeline_result.result_for_solid('hello_world')

    assert result.success

    assert result.transformed_value().to_dict('list') == {
        'num1': [1, 3],
        'num2': [2, 4],
        'sum': [3, 7],
    }


def create_definition_based_solid():
    table_input = InputDefinition('num_csv', DataFrame)

    def transform_fn(_context, inputs):
        num_csv = inputs['num_csv']
        num_csv['sum'] = num_csv['num1'] + num_csv['num2']
        return num_csv

    # supports CSV and PARQUET by default
    hello_world = single_output_transform(
        name='hello_world',
        inputs=[table_input],
        transform_fn=transform_fn,
        output=OutputDefinition(DataFrame),
    )
    return hello_world


def create_decorator_based_solid():
    @lambda_solid(
        inputs=[InputDefinition('num_csv', DataFrame)], output=OutputDefinition(DataFrame)
    )
    def hello_world(num_csv):
        num_csv['sum'] = num_csv['num1'] + num_csv['num2']
        return num_csv

    return hello_world


def test_hello_world_decorator_style():
    hello_world = create_decorator_based_solid()
    run_hello_world(hello_world)
