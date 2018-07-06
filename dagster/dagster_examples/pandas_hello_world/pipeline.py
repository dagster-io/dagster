import dagster.core
from dagster.core.decorators import solid
import dagster.pandas_kernel as dagster_pd


@solid(
    inputs=[dagster_pd.dataframe_input('num', sources=[dagster_pd.csv_dataframe_source()])],
    output=dagster_pd.dataframe_output()
)
def sum_solid(num):
    sum_df = num.copy()
    sum_df['sum'] = sum_df['num1'] + sum_df['num2']
    return sum_df


@solid(
    inputs=[dagster_pd.dataframe_dependency(name='sum_df', solid=sum_solid)],
    output=dagster_pd.dataframe_output()
)
def sum_sq_solid(sum_df):
    sum_sq_df = sum_df.copy()
    sum_sq_df['sum_sq'] = sum_df['sum']**2
    return sum_sq_df


@solid(inputs=[dagster_pd.dataframe_dependency(sum_sq_solid)], output=dagster_pd.dataframe_output())
def always_fails_solid(**_kwargs):
    raise Exception('I am a programmer and I make error')


def define_pipeline():
    return dagster.core.pipeline(
        name='pandas_hello_world_fails', solids=[
            sum_solid,
            sum_sq_solid,
            always_fails_solid,
        ]
    )


def define_success_pipeline():
    return dagster.core.pipeline(
        name='pandas_hello_world', solids=[
            sum_solid,
            sum_sq_solid,
        ]
    )
