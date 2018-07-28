import pandas as pd

import dagster
from dagster import config
from dagster.core import types
from dagster.core.definitions import (
    InputDefinition,
    MaterializationDefinition,
    OutputDefinition,
    SolidDefinition,
    SourceDefinition,
    ArgumentDefinition,
)
from dagster.core.execution import (ExecutionContext, execute_single_solid)
from dagster.utils.test import script_relative_path


def create_test_context():
    return ExecutionContext()


def create_hello_world_solid_no_api():
    def hello_world_transform_fn(_context, args):
        num_df = args['num_df']
        num_df['sum'] = num_df['num1'] + num_df['num2']
        return num_df

    csv_input = InputDefinition(
        name='num_df',
        sources=[
            SourceDefinition(
                source_type='CSV',
                argument_def_dict={'path': ArgumentDefinition(types.Path)},
                source_fn=lambda context, arg_dict: pd.read_csv(arg_dict['path']),
            ),
        ],
    )

    csv_materialization = MaterializationDefinition(
        name='CSV',
        materialization_fn=lambda df, arg_dict: df.to_csv(arg_dict['path'], index=False),
        argument_def_dict={'path': ArgumentDefinition(types.Path)}
    )

    hello_world = SolidDefinition(
        name='hello_world',
        inputs=[csv_input],
        transform_fn=hello_world_transform_fn,
        output=OutputDefinition(materializations=[csv_materialization])
    )
    return hello_world


def test_hello_world_no_library_support():
    hello_world = create_hello_world_solid_no_api()

    result = execute_single_solid(
        create_test_context(),
        hello_world,
        environment=config.Environment(
            sources={
                'hello_world': {
                    'num_df': config.Source('CSV', {'path': script_relative_path('num.csv')})
                }
            }
        ),
    )

    assert result.success

    assert result.transformed_value.to_dict('list') == {
        'num1': [1, 3],
        'num2': [2, 4],
        'sum': [3, 7],
    }


def create_dataframe_input(name):
    return InputDefinition(
        name=name,
        sources=[
            SourceDefinition(
                source_type='CSV',
                argument_def_dict={'path': ArgumentDefinition(types.Path)},
                source_fn=lambda context, arg_dict: pd.read_csv(arg_dict['path']),
            ),
        ],
    )


def create_dataframe_dependency(name, depends_on):
    return InputDefinition(
        name=name,
        sources=[
            SourceDefinition(
                source_type='CSV',
                argument_def_dict={'path': ArgumentDefinition(types.Path)},
                source_fn=lambda context, arg_dict: pd.read_csv(arg_dict['path']),
            ),
        ],
        depends_on=depends_on,
    )


def create_dataframe_output():
    def mat_fn(_context, arg_dict, df):
        df.to_csv(arg_dict['path'], index=False)

    return OutputDefinition(
        materializations=[
            MaterializationDefinition(
                name='CSV',
                materialization_fn=mat_fn,
                argument_def_dict={'path': ArgumentDefinition(types.Path)},
            ),
        ],
    )


def create_hello_world_solid_composed_api():
    def transform_fn(_context, args):
        num_df = args['num_df']
        num_df['sum'] = num_df['num1'] + num_df['num2']
        return num_df

    hello_world = SolidDefinition(
        name='hello_world',
        inputs=[create_dataframe_input(name='num_df')],
        transform_fn=transform_fn,
        output=create_dataframe_output(),
    )
    return hello_world


def test_hello_world_composed():
    hello_world = create_hello_world_solid_composed_api()

    result = execute_single_solid(
        create_test_context(),
        hello_world,
        environment=config.Environment(
            sources={
                'hello_world': {
                    'num_df': config.Source('CSV', {'path': script_relative_path('num.csv')})
                }
            }
        ),
    )

    assert result.success

    assert result.transformed_value.to_dict('list') == {
        'num1': [1, 3],
        'num2': [2, 4],
        'sum': [3, 7],
    }


def test_pipeline():
    def solid_one_transform(_context, args):
        num_df = args['num_df']
        num_df['sum'] = num_df['num1'] + num_df['num2']
        return num_df

    solid_one = SolidDefinition(
        name='solid_one',
        inputs=[create_dataframe_input(name='num_df')],
        transform_fn=solid_one_transform,
        output=create_dataframe_output(),
    )

    def solid_two_transform(_context, args):
        sum_df = args['sum_df']
        sum_df['sum_sq'] = sum_df['sum'] * sum_df['sum']
        return sum_df

    solid_two = SolidDefinition(
        name='solid_two',
        inputs=[create_dataframe_dependency(name='sum_df', depends_on=solid_one)],
        transform_fn=solid_two_transform,
        output=create_dataframe_output(),
    )

    pipeline = dagster.PipelineDefinition(solids=[solid_one, solid_two])

    environment = config.Environment(
        sources={
            'solid_one': {
                'num_df': config.Source('CSV', {'path': script_relative_path('num.csv')})
            }
        }
    )

    execute_pipeline_result = dagster.execute_pipeline(
        pipeline,
        environment=environment,
    )

    assert execute_pipeline_result.result_named('solid_two').transformed_value.to_dict('list') == {
        'num1': [1, 3],
        'num2': [2, 4],
        'sum': [3, 7],
        'sum_sq': [9, 49],
    }

    sum_sq_path_args = {'path': '/tmp/sum_sq.csv'}
    environment_two = config.Environment(
        sources={
            'solid_one': {
                'num_df': config.Source('CSV', {'path': script_relative_path('num.csv')})
            }
        },
        materializations=[
            config.Materialization(
                solid='solid_two',
                name='CSV',
                args=sum_sq_path_args,
            ),
        ]
    )

    dagster.execute_pipeline(pipeline, environment=environment_two)

    sum_sq_df = pd.read_csv('/tmp/sum_sq.csv')

    assert sum_sq_df.to_dict('list') == {
        'num1': [1, 3],
        'num2': [2, 4],
        'sum': [3, 7],
        'sum_sq': [9, 49],
    }
