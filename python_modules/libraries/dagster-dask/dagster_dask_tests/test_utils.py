from dagster import (
    InputDefinition,
    execute_solid,
    file_relative_path,
    solid,
)
import dask.dataframe as dd

from dagster_dask import DataFrame


@solid(input_defs=[InputDefinition(dagster_type=DataFrame, name="input_df")])
def passthrough(_, input_df: DataFrame) -> DataFrame:
    return input_df


def generate_config(path, **df_opts):
    return {
        "solids": {
            "passthrough": {
                "inputs": {
                    "input_df": {
                        "read": {
                            "csv": {
                                "path": path,
                            },
                        },
                        **df_opts,
                    },
                },
            },
        },
    }


def test_sample_utility():
    path = file_relative_path(__file__, "num.csv")
    frac = 0.5

    input_df = dd.read_csv(path)

    run_config = generate_config(path, sample={"frac": 0.5})
    result = execute_solid(passthrough, run_config=run_config)
    output_df = result.output_value()

    assert len(input_df) * frac == len(output_df)
