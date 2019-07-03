from dagster import (
    DependencyDefinition,
    InputDefinition,
    OutputDefinition,
    PipelineDefinition,
    PresetDefinition,
    file_relative_path,
    lambda_solid,
)
import dagster_pandas as dagster_pd


@lambda_solid(
    input_defs=[InputDefinition('num', dagster_pd.DataFrame)],
    output_def=OutputDefinition(dagster_pd.DataFrame),
)
def sum_solid(num):
    sum_df = num.copy()
    sum_df['sum'] = sum_df['num1'] + sum_df['num2']
    return sum_df


@lambda_solid(
    input_defs=[InputDefinition('sum_df', dagster_pd.DataFrame)],
    output_def=OutputDefinition(dagster_pd.DataFrame),
)
def sum_sq_solid(sum_df):
    sum_sq_df = sum_df.copy()
    sum_sq_df['sum_sq'] = sum_df['sum'] ** 2
    return sum_sq_df


@lambda_solid(
    input_defs=[InputDefinition('sum_sq_solid', dagster_pd.DataFrame)],
    output_def=OutputDefinition(dagster_pd.DataFrame),
)
def always_fails_solid(**_kwargs):
    raise Exception('I am a programmer and I make error')


def define_failure_pipeline():
    return PipelineDefinition(
        name='pandas_hello_world_fails',
        solid_defs=[sum_solid, sum_sq_solid, always_fails_solid],
        dependencies={
            'sum_sq_solid': {'sum_df': DependencyDefinition(sum_solid.name)},
            'always_fails_solid': {'sum_sq_solid': DependencyDefinition(sum_sq_solid.name)},
        },
    )


def define_pandas_hello_world_pipeline():
    return PipelineDefinition(
        name='pandas_hello_world',
        solid_defs=[sum_solid, sum_sq_solid],
        dependencies={
            'sum_solid': {},
            'sum_sq_solid': {'sum_df': DependencyDefinition(sum_solid.name)},
        },
        preset_defs=[
            PresetDefinition(
                'test',
                environment_files=[
                    file_relative_path(__file__, 'environments/pandas_hello_world_test.yaml')
                ],
            ),
            PresetDefinition(
                'prod',
                environment_files=[
                    file_relative_path(__file__, 'environments/pandas_hello_world_prod.yaml')
                ],
            ),
        ],
    )
