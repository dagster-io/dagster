import dagster.core
import dagster.pandas_kernel as dagster_pd


def define_pipeline():
    def sum_transform_fn(num):
        sum_df = num.copy()
        sum_df['sum'] = sum_df['num1'] + sum_df['num2']
        return sum_df

    sum_solid = dagster_pd.dataframe_solid(
        name='sum',
        inputs=[dagster_pd.dataframe_input('num', sources=[dagster_pd.csv_dataframe_source()])],
        transform_fn=sum_transform_fn
    )

    def sum_sq_transform_fn(sum):
        sum_sq = sum.copy()
        sum_sq['sum_sq'] = sum['sum']**2
        return sum_sq

    sum_sq_solid = dagster_pd.dataframe_solid(
        name='sum_sq',
        inputs=[dagster_pd.dataframe_dependency(sum_solid)],
        transform_fn=sum_sq_transform_fn
    )

    def always_fails_transform_fn(*_args, **_kwargs):
        raise Exception('I am a programmer and I make error')

    always_fails_solid = dagster_pd.dataframe_solid(
        name='always_fails',
        inputs=[dagster_pd.dataframe_dependency(sum_solid)],
        transform_fn=always_fails_transform_fn
    )

    return dagster.core.pipeline(name='pandas_hello_world', solids=[sum_solid, sum_sq_solid])
