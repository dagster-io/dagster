import pandas as pd

from dagster import (
    ConfigDefinition,
    DependencyDefinition,
    Field,
    InputDefinition,
    OutputDefinition,
    PipelineDefinition,
    Result,
    SolidDefinition,
    config,
    execute_pipeline,
    types,
)

from dagster.core.test_utils import single_output_transform

from dagster.utils import script_relative_path


def define_read_csv_solid(name):
    def _t_fn(info, _inputs):
        yield Result(pd.read_csv(info.config['path']))

    return SolidDefinition(
        name=name,
        inputs=[],
        outputs=[OutputDefinition()],
        config_def=ConfigDefinition.config_dict({
            'path': Field(types.Path)
        }),
        transform_fn=_t_fn
    )


def define_to_csv_solid(name):
    def _t_fn(info, inputs):
        inputs['df'].to_csv(info.config['path'], index=False)

    return SolidDefinition(
        name=name,
        inputs=[InputDefinition('df')],
        outputs=[],
        config_def=ConfigDefinition.config_dict({
            'path': Field(types.Path)
        }),
        transform_fn=_t_fn,
    )


def test_hello_world_pipeline_no_api():
    def hello_world_transform_fn(_context, inputs):
        num_df = inputs['num_df']
        num_df['sum'] = num_df['num1'] + num_df['num2']
        return num_df

    read_csv_solid = define_read_csv_solid('read_csv_solid')

    hello_world = single_output_transform(
        name='hello_world',
        inputs=[InputDefinition('num_df')],
        transform_fn=hello_world_transform_fn,
        output=OutputDefinition(),
    )

    pipeline = PipelineDefinition(
        solids=[read_csv_solid, hello_world],
        dependencies={
            'hello_world': {
                'num_df': DependencyDefinition('read_csv_solid'),
            },
        }
    )

    pipeline_result = execute_pipeline(
        pipeline,
        config.Environment(
            solids={
                'read_csv_solid': config.Solid({
                    'path': script_relative_path('num.csv'),
                }),
            },
        ),
    )

    assert pipeline_result.success

    result = pipeline_result.result_for_solid('hello_world')

    assert result.transformed_value().to_dict('list') == {
        'num1': [1, 3],
        'num2': [2, 4],
        'sum': [3, 7],
    }


def create_hello_world_solid_composed_pipeline():
    def transform_fn(_context, inputs):
        num_df = inputs['num_df']
        num_df['sum'] = num_df['num1'] + num_df['num2']
        return num_df

    hello_world = single_output_transform(
        name='hello_world',
        inputs=[InputDefinition('num_df')],
        transform_fn=transform_fn,
        output=OutputDefinition(),
    )

    return PipelineDefinition(
        solids=[define_read_csv_solid('read_hello_world'), hello_world],
        dependencies={'hello_world': {
            'num_df': DependencyDefinition('read_hello_world')
        }}
    )


def test_hello_world_composed():
    pipeline = create_hello_world_solid_composed_pipeline()

    pipeline_result = execute_pipeline(
        pipeline,
        environment=config.Environment(
            solids={
                'read_hello_world': config.Solid({
                    'path': script_relative_path('num.csv')
                }),
            },
        ),
    )

    assert pipeline_result.success

    result = pipeline_result.result_for_solid('hello_world')

    assert result.success

    assert result.transformed_value().to_dict('list') == {
        'num1': [1, 3],
        'num2': [2, 4],
        'sum': [3, 7],
    }


def test_pandas_hello_no_library():
    def solid_one_transform(_context, inputs):
        num_df = inputs['num_df']
        num_df['sum'] = num_df['num1'] + num_df['num2']
        return num_df

    solid_one = single_output_transform(
        name='solid_one',
        inputs=[InputDefinition(name='num_df')],
        transform_fn=solid_one_transform,
        output=OutputDefinition(),
    )

    def solid_two_transform(_context, inputs):
        sum_df = inputs['sum_df']
        sum_df['sum_sq'] = sum_df['sum'] * sum_df['sum']
        return sum_df

    solid_two = single_output_transform(
        name='solid_two',
        inputs=[InputDefinition(name='sum_df')],
        transform_fn=solid_two_transform,
        output=OutputDefinition(),
    )

    pipeline = PipelineDefinition(
        solids=[define_read_csv_solid('read_one'), solid_one, solid_two],
        dependencies={
            'solid_one': {
                'num_df': DependencyDefinition('read_one'),
            },
            'solid_two': {
                'sum_df': DependencyDefinition('solid_one'),
            },
        }
    )

    environment = config.Environment(
        solids={
            'read_one': config.Solid({
                'path': script_relative_path('num.csv')
            }),
        }
    )

    execute_pipeline_result = execute_pipeline(
        pipeline,
        environment=environment,
    )

    assert execute_pipeline_result.result_for_solid('solid_two'
                                                    ).transformed_value().to_dict('list') == {
                                                        'num1': [1, 3],
                                                        'num2': [2, 4],
                                                        'sum': [3, 7],
                                                        'sum_sq': [9, 49],
                                                    }

    sum_sq_out_path = '/tmp/sum_sq.csv'
    import os
    if os.path.exists(sum_sq_out_path):
        os.remove(sum_sq_out_path)

    sum_sq_path_args = {'path': '/tmp/sum_sq.csv'}
    environment_two = config.Environment(
        solids={
            'read_one': config.Solid({
                'path': script_relative_path('num.csv')
            }),
            'write_two': config.Solid(sum_sq_path_args),
        },
    )

    pipeline_two = PipelineDefinition(
        solids=[
            define_read_csv_solid('read_one'),
            solid_one,
            solid_two,
            define_to_csv_solid('write_two'),
        ],
        dependencies={
            'solid_one': {
                'num_df': DependencyDefinition('read_one'),
            },
            'solid_two': {
                'sum_df': DependencyDefinition('solid_one'),
            },
            'write_two': {
                'df': DependencyDefinition('solid_two'),
            }
        }
    )

    execute_pipeline(pipeline_two, environment=environment_two)

    sum_sq_df = pd.read_csv('/tmp/sum_sq.csv')

    assert sum_sq_df.to_dict('list') == {
        'num1': [1, 3],
        'num2': [2, 4],
        'sum': [3, 7],
        'sum_sq': [9, 49],
    }
