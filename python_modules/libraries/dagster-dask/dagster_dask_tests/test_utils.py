from dagster import (
    InputDefinition,
    execute_solid,
    file_relative_path,
    solid,
)

from dagster_dask import DataFrame


@solid(input_defs=[InputDefinition(dagster_type=DataFrame, name="input_df")])
def passthrough(_, input_df: DataFrame) -> DataFrame:
    return input_df


def test_single_utilities():
    file_name = file_relative_path(__file__, "num.csv")
    
    def generate_config(**df_opts):
        return {
            "solids": {
                "passthrough": {
                    "inputs": {
                        "input_df": {
                            "read": {
                                "csv": {
                                    "path": file_name,
                                },
                            },
                            **df_opts,
                        },
                    },
                },
            },
        }

    run_config = generate_config(sample={"frac": 0.5})
    result = execute_solid(passthrough, run_config=run_config)

    df = result.output_value()
    assert len(df) == 1
