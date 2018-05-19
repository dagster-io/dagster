import solidic
import solidic_pandas as solidic_pd


def define_pipeline():
    def sum_transform_fn(num_csv):
        sum_df = num_csv.copy()
        sum_df['sum'] = sum_df['num1'] + sum_df['num2']
        return sum_df

    sum_solid = solidic_pd.dataframe_solid(
        name='sum', inputs=[solidic_pd.csv_input('num_csv')], transform_fn=sum_transform_fn
    )

    def sum_sq_transform_fn(sum):
        sum_sq = sum.copy()
        sum_sq['sum_sq'] = sum['sum']**2
        return sum_sq

    sum_sq_solid = solidic_pd.dataframe_solid(
        name='sum_sq', inputs=[solidic_pd.depends_on(sum_solid)], transform_fn=sum_sq_transform_fn
    )

    def always_fails_transform_fn(*_args, **_kwargs):
        raise Exception('I am a programmer and I make error')

    always_fails_solid = solidic_pd.dataframe_solid(
        name='always_fails',
        inputs=[solidic_pd.depends_on(sum_solid)],
        transform_fn=always_fails_transform_fn
    )

    return solidic.pipeline(
        name='pandas_hello_world', solids=[sum_solid, sum_sq_solid, always_fails_solid]
    )


if __name__ == '__main__':
    from dagster.embedded_cli import embedded_dagster_single_pipeline_cli_main
    import sys

    embedded_dagster_single_pipeline_cli_main(sys.argv, define_pipeline())
