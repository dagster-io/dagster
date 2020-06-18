import pandas as pd
from dagster_pandas import DataFrame

from dagster import PresetDefinition, pipeline, solid


@solid
def read_csv(_, path: str) -> DataFrame:
    return pd.read_csv(path)


@solid
def sum_solid(_, num_df: DataFrame) -> DataFrame:
    sum_df = num_df.copy()
    sum_df['sum'] = sum_df['num1'] + sum_df['num2']
    return sum_df


@solid
def mult_solid(_, num_df: DataFrame) -> DataFrame:
    mult_df = num_df.copy()
    mult_df['mult'] = num_df['num1'] * num_df['num2']
    return mult_df


@solid
def sum_sq_solid(_, sum_df: DataFrame, mult_df: DataFrame) -> DataFrame:
    sum_sq_df = sum_df.copy()
    sum_sq_df['sum_sq'] = sum_df['sum'] ** 2
    sum_sq_df['sum_mult_sq'] = sum_df['sum'] * mult_df['mult']
    return sum_sq_df


@pipeline(
    description='Demo pipeline showcasing `dagster_pandas.Dataframe` types as solid inputs/outputs.',
    preset_defs=[
        PresetDefinition.from_pkg_resources(
            'test',
            pkg_resource_defs=[
                ('dagster_examples.toys.environments', 'pandas_hello_world_test.yaml')
            ],
        ),
        PresetDefinition.from_pkg_resources(
            'prod',
            pkg_resource_defs=[
                ('dagster_examples.toys.environments', 'pandas_hello_world_prod.yaml')
            ],
        ),
    ],
)
def pandas_hello_world_pipeline():
    return sum_sq_solid(sum_df=sum_solid(), mult_df=mult_solid())


@pipeline(
    description=(
        'Demo pipeline showcasing `dagster_pandas.Dataframe` types as solid inputs/outputs, using '
        'the same csv path for all root inputs.'
    )
)
def pandas_hello_world_pipeline_with_read_csv():
    csv = read_csv()
    return sum_sq_solid(sum_df=sum_solid(csv), mult_df=mult_solid(csv))
