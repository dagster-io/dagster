import dagster_pandas as dagster_pd
from dagster import (
    InputDefinition,
    OutputDefinition,
    PresetDefinition,
    file_relative_path,
    lambda_solid,
    pipeline,
)


@lambda_solid(
    input_defs=[InputDefinition("num", dagster_pd.DataFrame)],
    output_def=OutputDefinition(dagster_pd.DataFrame),
)
def sum_solid(num):
    sum_df = num.copy()
    sum_df["sum"] = sum_df["num1"] + sum_df["num2"]
    return sum_df


@lambda_solid(
    input_defs=[InputDefinition("sum_df", dagster_pd.DataFrame)],
    output_def=OutputDefinition(dagster_pd.DataFrame),
)
def sum_sq_solid(sum_df):
    sum_sq_df = sum_df.copy()
    sum_sq_df["sum_sq"] = sum_df["sum"] ** 2
    return sum_sq_df


@lambda_solid(
    input_defs=[InputDefinition("sum_sq_solid", dagster_pd.DataFrame)],
    output_def=OutputDefinition(dagster_pd.DataFrame),
)
def always_fails_solid(**_kwargs):
    raise Exception("I am a programmer and I make error")


@pipeline
def pandas_hello_world_fails():
    always_fails_solid(sum_sq_solid=sum_sq_solid(sum_df=sum_solid()))


@pipeline(
    preset_defs=[
        PresetDefinition.from_files(
            "test",
            config_files=[
                file_relative_path(__file__, "environments/pandas_hello_world_test.yaml")
            ],
        ),
        PresetDefinition.from_files(
            "prod",
            config_files=[
                file_relative_path(__file__, "environments/pandas_hello_world_prod.yaml")
            ],
        ),
    ]
)
def pandas_hello_world():
    sum_sq_solid(sum_solid())
