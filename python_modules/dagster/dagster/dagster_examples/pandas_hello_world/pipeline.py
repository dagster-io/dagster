import dagster
from dagster import (solid, InputDefinition, OutputDefinition, PipelineDefinition)
import dagster.pandas_kernel as dagster_pd


@solid(
    inputs=[InputDefinition('num', dagster_pd.DataFrame)],
    output=OutputDefinition(dagster_pd.DataFrame)
)
def sum_solid(num):
    sum_df = num.copy()
    sum_df['sum'] = sum_df['num1'] + sum_df['num2']
    return sum_df


@solid(
    inputs=[InputDefinition('sum_df', dagster_pd.DataFrame, depends_on=sum_solid)],
    output=OutputDefinition(dagster_pd.DataFrame)
)
def sum_sq_solid(sum_df):
    sum_sq_df = sum_df.copy()
    sum_sq_df['sum_sq'] = sum_df['sum']**2
    return sum_sq_df


@solid(
    inputs=[InputDefinition('sum_sq_solid', dagster_pd.DataFrame, depends_on=sum_sq_solid)],
    output=OutputDefinition(dagster_pd.DataFrame)
)
def always_fails_solid(**_kwargs):
    raise Exception('I am a programmer and I make error')


def define_pipeline():
    return dagster.PipelineDefinition(
        name='pandas_hello_world_fails',
        solids=[
            sum_solid,
            sum_sq_solid,
            always_fails_solid,
        ],
    )


def define_success_pipeline():
    return PipelineDefinition(name='pandas_hello_world', solids=[sum_solid, sum_sq_solid])
