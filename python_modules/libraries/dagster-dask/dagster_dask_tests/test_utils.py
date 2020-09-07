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


def test_sample():
    path = file_relative_path(__file__, "canada.csv")
    frac = 0.25

    input_df = dd.read_csv(path)

    run_config = generate_config(path, sample={"frac": frac})
    result = execute_solid(passthrough, run_config=run_config)
    output_df = result.output_value()

    assert len(input_df) * frac == len(output_df)


def test_reset_index():
    path = file_relative_path(__file__, "canada.csv")

    input_df = dd.read_csv(path)

    # Reset the index without dropping. We expect the index to be moved
    # to the columns, as a column named "index".
    run_config = generate_config(path, reset_index={})
    result = execute_solid(passthrough, run_config=run_config)
    output_df = result.output_value()
    assert "index" in output_df.columns
    assert len(output_df.columns) == len(input_df.columns) + 1


def test_set_index():
    path = file_relative_path(__file__, "canada.csv")
    col = "ID"
    
    input_df = dd.read_csv(path)
    assert col in input_df.columns
    
    # Set index to ID. We expect the column to be dropped by default.
    run_config = generate_config(path, set_index={"other": col})
    result = execute_solid(passthrough, run_config=run_config)
    output_df = result.output_value()
    assert col not in output_df.columns

    # Set index to ID without dropping the column.
    run_config = generate_config(path, set_index={"other": col, "drop": False})
    result = execute_solid(passthrough, run_config=run_config)
    output_df = result.output_value()
    assert col in output_df.columns


def test_repartition():
    path = file_relative_path(__file__, "canada.csv")
    npartitions = 2

    input_df = dd.read_csv(path)
    assert input_df.npartitions == 1

    # Repartition from 1 to 2 partitions.
    run_config = generate_config(path, repartition={"npartitions": npartitions})
    result = execute_solid(passthrough, run_config=run_config)
    output_df = result.output_value()
    assert output_df.npartitions == npartitions


def test_sanitize_column_names():
    path = file_relative_path(__file__, "canada.csv")

    input_df = dd.read_csv(path)
    assert all(col in input_df.columns for col in ("ID", "provinceOrTerritory", "country"))

    # Set sanitize_column_names=False to not modify the column names
    run_config = generate_config(path, sanitize_column_names=False)
    result = execute_solid(passthrough, run_config=run_config)
    output_df = result.output_value()
    assert all(col in output_df.columns for col in ("ID", "provinceOrTerritory", "country"))

    # Set sanitize_column_names=True to modify the column names
    run_config = generate_config(path, sanitize_column_names=True)
    result = execute_solid(passthrough, run_config=run_config)
    output_df = result.output_value()
    assert all(col in output_df.columns for col in ("id", "provinceorterritory", "country"))
